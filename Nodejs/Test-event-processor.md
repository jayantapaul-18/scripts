To test the event processor, we'll add logic to simulate incoming events from all three sources: a file, an API endpoint, and a message queue. 

### Step 1: Create Test Data for File-Based Events

First, create a file named `events.json` that will be used by the file listener to detect and process events.

**`events.json`**

```json
[
  { "id": 1, "type": "file", "message": "Event from file 1" },
  { "id": 2, "type": "file", "message": "Event from file 2" }
]
```

### Step 2: Create a Script to Simulate API and Queue Events

We'll create a test script to send events via the API and queue (RabbitMQ). The script will use `axios` to send HTTP POST requests to the API endpoint and `amqplib` to publish messages to RabbitMQ.

**`testEventProcessor.js`**

```javascript
const axios = require('axios');
const amqp = require('amqplib');

// API Event Simulation
async function simulateApiEvents(apiUrl) {
    try {
        const events = [
            { id: 3, type: 'api', message: 'Event from API 1' },
            { id: 4, type: 'api', message: 'Event from API 2' }
        ];

        for (const event of events) {
            await axios.post(apiUrl, event);
            console.log(`Sent event to API: ${JSON.stringify(event)}`);
        }
    } catch (error) {
        console.error('Error sending event to API:', error.message);
    }
}

// Queue Event Simulation
async function simulateQueueEvents(amqpUrl, queueName) {
    try {
        const connection = await amqp.connect(amqpUrl);
        const channel = await connection.createChannel();
        await channel.assertQueue(queueName, { durable: false });

        const events = [
            { id: 5, type: 'queue', message: 'Event from Queue 1' },
            { id: 6, type: 'queue', message: 'Event from Queue 2' }
        ];

        for (const event of events) {
            channel.sendToQueue(queueName, Buffer.from(JSON.stringify(event)));
            console.log(`Sent event to queue: ${JSON.stringify(event)}`);
        }

        setTimeout(() => {
            connection.close();
            console.log('Queue simulation completed.');
        }, 500);
    } catch (error) {
        console.error('Error sending event to queue:', error.message);
    }
}

// Run Test Simulations
(async () => {
    const apiUrl = 'http://localhost:3000/event';
    const amqpUrl = 'amqp://localhost';
    const queueName = 'event_queue';

    // Simulate events for API
    await simulateApiEvents(apiUrl);

    // Simulate events for Queue
    await simulateQueueEvents(amqpUrl, queueName);
})();
```

### Step 3: Run the Test Simulation

Make sure the event processor is running by executing `node server.js`. Once it's running, run the test script:

```bash
node testEventProcessor.js
```

### Step 4: Explanation of the Test Logic

1. **API Event Simulation**: Sends HTTP POST requests to the API endpoint (`/event`) using `axios`. Each request represents an event from the API source.
2. **Queue Event Simulation**: Publishes messages to RabbitMQ using `amqplib`. Each message represents an event from the queue source.
3. **File Event Simulation**: The file events are simulated by modifying the `events.json` file manually or programmatically. The file listener (`fs.watchFile`) will detect changes and process the events.

### Step 5: Automate File Event Changes (Optional)

You can automate file event changes to simulate continuous incoming events. Here's a script to modify the `events.json` file periodically:

**`simulateFileEvents.js`**

```javascript
const fs = require('fs');

function simulateFileEventChanges(filePath) {
    let counter = 3;
    setInterval(() => {
        const newEvent = { id: counter++, type: 'file', message: `New event from file ${counter}` };
        const fileData = JSON.stringify([newEvent], null, 2);
        fs.writeFileSync(filePath, fileData);
        console.log(`Modified file with new event: ${JSON.stringify(newEvent)}`);
    }, 5000); // Change every 5 seconds
}

// Start the simulation
simulateFileEventChanges('./events.json');
```

Run this script to simulate file events dynamically:

```bash
node simulateFileEvents.js
```

### Conclusion

By running these test scripts, you can simulate events from all three sources — a file, an API endpoint, and a queue. This allows you to thoroughly test the event processing system and ensure it handles various input methods correctly.
