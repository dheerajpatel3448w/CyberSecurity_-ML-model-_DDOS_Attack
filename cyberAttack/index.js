import express from "express"
import fs from "fs"
import csv from "csv-parser"
const app= express();
import { Kafka } from 'kafkajs'

const kafka = new Kafka({
  clientId: 'network-sensor',
  brokers: ['localhost:9092']
});

const producer = kafka.producer();

async function streamData() {
  await producer.connect();
  console.log('✅ Connected to Kafka Broker');

  let count = 0;
  
  fs.createReadStream('cicids2017_cleaned.csv')
    .pipe(csv())
    .on('data', async (row) => {
      try {
        const payload = JSON.stringify(row);
        await producer.send({
          topic: 'network-traffic',
          messages: [{ key: `packet-${count}`, value: payload }],
        });

        count++;
        if (count % 1000 === 0) console.log(`🚀 Streamed ${count} packets to Kafka...`);
      } catch (error) {
        console.error('Error sending message:', error);
      }
    })
    .on('end', () => console.log('🏁 Finished streaming dataset.'));
}

streamData().catch(console.error);

app.listen(5001,()=>{
    console.log("sever running");
})