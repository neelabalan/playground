package elevator

import (
	"sync"
)

type Elevator struct {
	ID           int
	CurrentFloor int
	Direction    int // -1 for down, 1 for up, 0 for idle
	Requests     []int
	mu           sync.Mutex
}

type Building struct {
	Floors    int
	Elevators []*Elevator
	mu        sync.Mutex
}

func (e *Elevator) AddRequest(floor int) {
	e.mu.Lock()
	e.Requests = append(e.Requests, floor)
	e.mu.Unlock()
}

func (e *Elevator) Move() {
	e.mu.Lock()
	if len(e.Requests) > 0 {
		target := e.Requests[0]
		if e.CurrentFloor < target {
			e.Direction = 1
			e.CurrentFloor++
		} else if e.CurrentFloor > target {
			e.Direction = -1
			e.CurrentFloor--
		} else {
			e.Direction = 0
			e.Requests = e.Requests[1:]
		}
	} else {
		e.Direction = 0
	}
	e.mu.Unlock()

}

func (b *Building) AddRequest(floor int) {
	b.mu.Lock()
	defer b.mu.Unlock()

	// Simple dispatch strategy: assign to the first idle or nearest elevator
	for _, elevator := range b.Elevators {
		if elevator.Direction == 0 {
			elevator.AddRequest(floor)
			return
		}
	}

	nearestElevator := b.Elevators[0]
	minDistance := abs(b.Elevators[0].CurrentFloor - floor)
	for _, elevator := range b.Elevators {
		distance := abs(elevator.CurrentFloor - floor)
		if distance < minDistance {
			nearestElevator = elevator
			minDistance = distance
		}
	}
	nearestElevator.AddRequest(floor)
}

func abs(x int) int {
	if x < 0 {
		return -x
	}
	return x
}
