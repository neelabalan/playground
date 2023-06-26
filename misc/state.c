// From chatgpt
#include <stdio.h>

// Function declarations
void handleStateIdle();
void handleStateLogic1();
void handleStateLogic2();
void handleStateLogic3();

// Function pointer type for state handlers
typedef void (*StateHandler)();

// State handler array
StateHandler stateHandlers[] = {
    handleStateIdle,
    handleStateLogic1,
    handleStateLogic2,
    handleStateLogic3
};

// Define the states
typedef enum {
    STATE_IDLE,
    STATE_LOGIC1,
    STATE_LOGIC2,
    STATE_LOGIC3,
    NUM_STATES
} State;

int main() {
    State currentState = STATE_IDLE;
    for(int i=0; i<3; i++) {
        // Call the state handler for the current state
        stateHandlers[currentState]();

        // Transition to the next state
        currentState = (currentState + 1) % NUM_STATES;
    }

    return 0;
}

// Function definitions
void handleStateIdle() {
    printf("Handling IDLE state...\n");
    // Perform actions for IDLE state
}

void handleStateLogic1() {
    printf("Handling LOGIC1 state...\n");
    // Perform actions for LOGIC1 state
}

void handleStateLogic2() {
    printf("Handling LOGIC2 state...\n");
    // Perform actions for LOGIC2 state
}

void handleStateLogic3() {
    printf("Handling LOGIC3 state...\n");
    // Perform actions for LOGIC3 state
}
