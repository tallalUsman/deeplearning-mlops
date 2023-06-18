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
	"time"
	"os"
)

const (
	baseURL = "https://api-football-v1.p.rapidapi.com/v3/fixtures?date=%v"
	baseURL_stats = "https://api-football-v1.p.rapidapi.com/v3/fixtures/statistics?fixture=%d"
	bucketName = "football_data_api" // replace with your bucket name
)

type Result struct {
	Date string
	Data []byte
}

type ResultTWO struct {
    Date string
    Data interface{}
}

type APIResponse struct {
	Response []struct {
		Fixture struct {
			ID int `json:"id"`
		} `json:"fixture"`
	} `json:"response"`
}


func main() {
	dates, err := getDailyDates("2014-08-01", "2014-12-01")
	if err != nil {
		panic(err)
	}

	ctx := context.Background()
	client, err := storage.NewClient(ctx)

	defer client.Close()

	numGoroutines := 3 // use number of CPUs as number of goroutines
	results := make(chan Result)
	datesChan := make(chan string)

	var wg sync.WaitGroup

	// Start concurrent goroutines to make API requests
	for i := 0; i < numGoroutines; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for date := range datesChan {
				url := fmt.Sprintf(baseURL, date)
				data, err := makeAPIRequest(url)
				if err == nil {
					results <- Result{Date: date, Data: data}
				}
				time.Sleep(1 * time.Second)
			}
		}()
	}

	go func() {
		for _, date := range dates {
			datesChan <- date
		}
		close(datesChan)
	}()

	go func() {
		wg.Wait()
		close(results)
	}()
	
	// Collect the results
	for result := range results {        
		// Format JSON data
  //      fmt.Printf("Data for date %s: %s\n", result.Date, string(result.Data))
		var prettyJSON bytes.Buffer
		err := json.Indent(&prettyJSON, result.Data, "", "  ")
		if err != nil {
			fmt.Printf("Failed to format JSON data for date %s: %v\n", result.Date, err)
			continue
		}

		err = writeToGCS_fixtures(ctx, client, result.Date, prettyJSON.Bytes())
		if err != nil {
			fmt.Printf("Failed to write data for date %s: %v\n", result.Date, err)
			}

        // Parse the fixture IDs
        var apiRes APIResponse
        if err := json.Unmarshal(result.Data, &apiRes); err != nil {
            fmt.Printf("Failed to parse fixture IDs for date %s: %v\n", result.Date, err)
            continue
        }
        
        // Get the fixture IDs
        fixtureIDs := make(chan int)
        fixtureRes := make(chan Result)
		var ag sync.WaitGroup

        // Start goroutines for the fixture API calls
        for i := 0; i < numGoroutines; i++ {
            ag.Add(1)
            go func() {
                defer ag.Done()
                for id := range fixtureIDs {
                    url := fmt.Sprintf(baseURL_stats, id)
    //                fmt.Printf(string(url))
                    data, err := makeAPIRequest(url)
                    if err == nil {
                        fixtureRes <- Result{Date: result.Date, Data: data}
                    }
					time.Sleep(1 * time.Second)
                }
            }()
        }
        
        // Send the fixture IDs to the channel
        go func() {
            for _, resp := range apiRes.Response {
                fixtureIDs <- resp.Fixture.ID
            }
            close(fixtureIDs)
        }()

        // Wait for the fixture API calls to finish and then close the results channel
        go func() {
            ag.Wait()
            close(fixtureRes)
        }()
        
		var allFixtureData []ResultTWO
        // Collect the fixture results
        for res := range fixtureRes {
			var jsonData map[string]interface{} 
			if err := json.Unmarshal(res.Data, &jsonData); err != nil {
				fmt.Printf("Failed to unmarshal JSON data for date %s: %v\n", res.Date, err)
				continue
			}
			// Combine different ones together
		
			// Create a ResultTWO and append it to allFixtureData
			resTwo := ResultTWO{Date: res.Date, Data: jsonData}
			allFixtureData = append(allFixtureData, resTwo)
			}
        
		jsonData, err := json.MarshalIndent(allFixtureData, "", "  ")
        fmt.Printf("All fixture data: %s\n", jsonData)
        if err != nil {
            fmt.Printf("Failed to convert fixture data to JSON: %v\n", err)
            continue
        }

		jsonDataBytes := []byte(jsonData)

		err = writeToGCS_stat(ctx, client, result.Date, jsonDataBytes)
		if err != nil {
			fmt.Printf("Failed to write data for date %s: %v\n", result.Date, err)
			}
		
	}
}

// other functions...

func writeToGCS_stat(ctx context.Context, client *storage.Client, date string, data []byte) error {
	objectName := fmt.Sprintf("raw/fixture-stats/%s/%s.json", date, date)  // Creates "folder" for each date

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

func writeToGCS_fixtures(ctx context.Context, client *storage.Client, date string, data []byte) error {
	objectName := fmt.Sprintf("raw/fixtures/%s/%s.json", date, date)  // Creates "folder" for each date

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
	req.Header.Add("X-RapidAPI-Key", "fbd410bba0mshcda5e4098c490e1p1617c7jsnd3b671676e3d")
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

func getDailyDates(start, end string) ([]string, error) {
	layout := "2006-01-02"
	startDate, err := time.Parse(layout, start)
	if err != nil {
		return nil, err
	}
	endDate, err := time.Parse(layout, end)
	if err != nil {
		return nil, err
	}

	var result []string

    for startDate.Before(endDate.AddDate(0, 0, 1)) { // Add one day to include end date in the result
        result = append(result, startDate.Format(layout))
        // Adding 1 day to start the next day
        startDate = startDate.AddDate(0, 0, 1)
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