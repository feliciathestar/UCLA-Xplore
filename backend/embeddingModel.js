const axios = require('axios');

async function getEmbedding(text) {
  // Replace with your embedding model API call
  const response = await axios.post('https://embedding-model-api', { text });
  return response.data.embedding;
}

async function searchSimilarities(embedding) {
  // Replace with your similarity search API call
  const response = await axios.post('https://similarity-search-api', { embedding });
  return response.data.results;
}

module.exports = { getEmbedding, searchSimilarities };