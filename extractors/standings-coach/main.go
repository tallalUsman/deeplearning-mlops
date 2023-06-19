package main

import (
	"bytes"
	"context"
	"cloud.google.com/go/storage"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"sync"
	"os"
	"strconv"
)

const (
	baseURL = "https://api-football-v1.p.rapidapi.com/v3/standings?season=%s&league=%d"
	baseURL_coach = "https://api-football-v1.p.rapidapi.com/v3/coachs?team=%d"
	bucketName = "football_data_api" // replace with your bucket name
)

type Result struct {
	Date string
	League int
	Data []byte
}

type ResultTWO struct {
    TeamID int
	Data []byte
}

type RequestInfo struct {
	Date     string
	LeagueID int
}

type APIResponse struct {
	Response []struct {
		League struct {
			LeagueID        int    `json:"id"`
			Standings [][]struct {
				Rank   int    `json:"rank"`
				Team   struct {
					TeamID   int    `json:"id"`
				} `json:"team"`
				} `json:"standings"`
				} `json:"league"`
			} `json:"response"`
		}

func main() {
	if len(os.Args) != 3 {
		fmt.Println("Usage: go run main.go [start_date] [end_date]")
		fmt.Println("Both dates must be in the format YYYY.")
		os.Exit(1)
	}
	startDate := os.Args[1]
	endDate := os.Args[2]



	dates, err := getYearlyDates(startDate, endDate)
	if err != nil {
		panic(err)
	}
	leagueIDs := []int{39, 135, 78, 140, 61, 71, 492, 203, 497, 40, 128, 144}


	ctx := context.Background()
	client, err := storage.NewClient(ctx)

	defer client.Close()

	numGoroutines := 4 // use number of CPUs as number of goroutines
	requestInfoChan := make(chan RequestInfo)
	results := make(chan Result)

	var wg sync.WaitGroup

	// Start concurrent goroutines to make API requests
	for i := 0; i < numGoroutines; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for info := range requestInfoChan {
				url := fmt.Sprintf(baseURL,  info.Date, info.LeagueID)
				data, err := makeAPIRequest(url)
				if err == nil {
					results <- Result{Date: info.Date, League: info.LeagueID, Data: data}
				}
			}
		}()
	}

	go func() {
		for _, date := range dates {
			for _, id := range leagueIDs {
				requestInfoChan <- RequestInfo{Date: date, LeagueID: id}
			}
		}
		close(requestInfoChan)
	}()

	go func() {
		wg.Wait()
		close(results)
	}()
	
	teamIDs := make(map[int]bool)
	// Collect the results
	for result := range results {        
		// Format JSON data
		var prettyJSON bytes.Buffer
		err := json.Indent(&prettyJSON, result.Data, "", "  ")
		if err != nil {
			fmt.Printf("Failed to format JSON data for date %s: %v\n", result.Date, err)
			continue
		}

		err = writeToGCS_standings(ctx, client, result.Date, result.League, prettyJSON.Bytes())
		if err != nil {
			fmt.Printf("Failed to write data for date %s: %v\n", result.Date, err)
		}

		fmt.Printf("All standing data: %s\n", prettyJSON.Bytes())

		var apiRes APIResponse
		if err := json.Unmarshal(result.Data, &apiRes); err != nil {
			fmt.Printf("Failed to parse team IDs for date %s: %v\n", result.Date, err)
			continue
		}

		for _, resp := range apiRes.Response {
			for _, standingGroup := range resp.League.Standings {
				for _, standing := range standingGroup {
					teamIDs[standing.Team.TeamID] = true
				}
			}
		}
			
		// After the loop, print unique team IDs
		for id := range teamIDs {
			fmt.Println(id)
			}
	}

	TeamIDs := make(chan int)
	CoachRes := make(chan ResultTWO)
        
	var ag sync.WaitGroup

    // Start goroutines for the coach API calls
    for i := 0; i < numGoroutines; i++ {
        ag.Add(1)
        go func() {
            defer ag.Done()
            for id := range TeamIDs {
                url := fmt.Sprintf(baseURL_coach, id)
                fmt.Printf(string(url))
                data, err := makeAPIRequest(url)
                if err == nil {
                    CoachRes <- ResultTWO{TeamID: id, Data: data}
                }
            }
        }()
    }
        
    // Send the team IDs to the channel
    go func() {
        for id := range teamIDs {
            TeamIDs <- id
        }
        close(TeamIDs)
    }()

     // Wait for the fixture API calls to finish and then close the results channel
    go func() {
        ag.Wait()
        close(CoachRes)
        }()
        
		
	// Collect the coachs results
    for res := range CoachRes {
		var prettyJSON bytes.Buffer
		err := json.Indent(&prettyJSON, res.Data, "", "  ")
		if err != nil {
			fmt.Printf("Failed to format JSON data for date %s: %v\n", res.TeamID, err)
			continue
		}
		
		err = writeToGCS_coach(ctx, client, res.TeamID, prettyJSON.Bytes())
		if err != nil {
			fmt.Printf("Failed to write data for date %s: %v\n", es.TeamID, err)
		 	}
		
		fmt.Printf("All coach data: %s\n", prettyJSON.Bytes())

		
	}
}

// other functions...

func writeToGCS_standings(ctx context.Context, client *storage.Client, date string, league int, data []byte) error {
	objectName := fmt.Sprintf("raw/standing/%d/%s.json", league, date)  // Creates "folder" for each date

	bucket := client.Bucket(bucketName)
	object := bucket.Object(objectName)
	writer := object.NewWriter(ctx)

	if _, err := writer.Write(data); err != nil {
		return err
	}
	if err := writer.Close(); err != nil {
		return err
	}
	return nil
}

func writeToGCS_coach(ctx context.Context, client *storage.Client, teamID int, data []byte) error {
	objectName := fmt.Sprintf("raw/coach/%d/%d.json", teamID, teamID)  // Creates "folder" for each date

	bucket := client.Bucket(bucketName)
	object := bucket.Object(objectName)
	writer := object.NewWriter(ctx)

	if _, err := writer.Write(data); err != nil {
		return err
	}
	if err := writer.Close(); err != nil {
		return err
	}
	return nil
}

func makeAPIRequest(url string) ([]byte, error) {
	req, _ := http.NewRequest("GET", url, nil)
	apiKey := os.Getenv("RAPID_API_KEY")
	req.Header.Add("X-RapidAPI-Key", apiKey)
	req.Header.Add("X-RapidAPI-Host", "api-football-v1.p.rapidapi.com")

	client := &http.Client{}
	res, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer res.Body.Close()

	body, err := ioutil.ReadAll(res.Body)
	if err != nil {
		return nil, err
	}

	return body, nil
}

func getYearlyDates(start, end string) ([]string, error) {
	startYear, err := strconv.Atoi(start)
	if err != nil {
		return nil, err
	}
	endYear, err := strconv.Atoi(end)
	if err != nil {
		return nil, err
	}

	var result []string

	for i := startYear; i <= endYear; i++ { 
		result = append(result, strconv.Itoa(i))
	}

	return result, nil
}


func saveJSON(filename string, data []byte) error {
    file, err := os.Create(filename)
    if err != nil {
        return err
    }
    defer file.Close()

    _, err = file.Write(data)
    if err != nil {
        return err
    }

    return nil
}