package main

import (
	"elevator_simulation/elevator"
	"log"
	"math/rand"
	"sync"
	"time"
)

func main() {
	r := rand.New(rand.NewSource(time.Now().UnixNano()))

	building := &elevator.Building{
		Floors: 10,
		Elevators: []*elevator.Elevator{
			{ID: 1, CurrentFloor: 0},
			{ID: 2, CurrentFloor: 0},
		},
	}

	var wg sync.WaitGroup

	// Elevator movement simulation
	for _, elev := range building.Elevators {
		wg.Add(1)
		go func(e *elevator.Elevator) {
			defer wg.Done()
			for i := 0; i < 100; i++ {
				e.Move()
				log.Printf("Elevator %d at floor %d\n", e.ID, e.CurrentFloor)
				time.Sleep(100 * time.Millisecond)
			}
		}(elev)
	}

	// Generate random requests
	wg.Add(1)
	go func() {
		defer wg.Done()
		for i := 0; i < 200; i++ {
			floor := r.Intn(building.Floors)
			building.AddRequest(floor)
			log.Printf("Request to floor %d\n", floor)
			// time.Sleep(500 * time.Millisecond)
		}
	}()

	wg.Wait()
}
