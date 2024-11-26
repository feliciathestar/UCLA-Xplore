const express = require('express');
const bodyParser = require('body-parser');
const mongoose = require('mongoose');
const { getEmbedding, searchSimilarities } = require('./embeddingModel');

const app = express();
app.use(bodyParser.json());

const cors = require('cors');
app.use(cors());

mongoose.connect('mongodb://localhost:27017/timeslots');

const TimeSlotSchema = new mongoose.Schema({
  date: String,
  time: String,
  isAvailable: Boolean,
  embedding: [Number]
});

const TimeSlot = mongoose.model('TimeSlot', TimeSlotSchema);

app.get('/api/availability', async (req, res) => {
  try {
    const slots = await TimeSlot.find();
    res.json(slots);
  } catch (err) {
    res.status(500).send('Failed to load availability');
  }
});

app.post('/api/availability', async (req, res) => {
  try {
    const { date, time, isAvailable } = req.body;
    const embedding = await getEmbedding(`${date} ${time} ${isAvailable}`);
    const slot = new TimeSlot({ date, time, isAvailable, embedding });
    await slot.save();
    res.status(200).send('Selection saved');
  } catch (err) {
    res.status(500).send('Failed to save selection');
  }
});

app.post('/api/availability/bulk', async (req, res) => {
  try {
    const { selections } = req.body;
    const slots = selections.map(async (selection) => {
      const embedding = await getEmbedding(`${selection.date} ${selection.time} ${selection.isAvailable}`);
      return new TimeSlot({ ...selection, embedding });
    });
    await TimeSlot.insertMany(await Promise.all(slots));
    res.status(200).send('Selections saved');
  } catch (err) {
    res.status(500).send('Failed to save selections');
  }
});

app.post('/api/search', async (req, res) => {
  try {
    const { query } = req.body;
    const queryEmbedding = await getEmbedding(query);
    const results = await searchSimilarities(queryEmbedding);
    res.json(results);
  } catch (err) {
    res.status(500).send('Failed to search');
  }
});

app.listen(3000, () => {
  console.log('Server is running on port 3000');
});