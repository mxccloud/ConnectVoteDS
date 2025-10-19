// api/verify-voter.js - Serverless function for Vercel
const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

module.exports = async (req, res) => {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version');

  // Handle preflight
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { id_number } = req.body;
    
    if (!id_number) {
      return res.status(400).json({ error: 'ID number is required' });
    }

    // For now, return simulated data since we can't run Selenium on Vercel
    const simulatedData = {
      status: 'success',
      identity_number: id_number,
      ward: 'Ward 12',
      voting_district: 'VD 1234',
      ward_number: '12',
      municipality: 'Johannesburg',
      province: 'Gauteng',
      processing_time: '2.5 seconds',
      note: 'This is simulated data. Backend requires Railway deployment for real IEC verification.'
    };

    res.status(200).json(simulatedData);
  } catch (error) {
    console.error('API error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};