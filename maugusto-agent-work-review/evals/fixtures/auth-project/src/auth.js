const express = require('express');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');
const router = express.Router();

const users = []; // in-memory store for now

function validatePassword(password) {
  if (password.length < 8) return false;
  // TODO: check uppercase and number requirements
  return true;
}

router.post('/register', async (req, res) => {
  const { email, password } = req.body;

  if (!email || !password) {
    return res.status(400).json({ error: 'Email and password required' });
  }

  const existing = users.find(u => u.email === email);
  if (existing) {
    return res.status(409).json({ error: 'Email already registered' });
  }

  if (!validatePassword(password)) {
    return res.status(400).json({ error: 'Invalid password' });
  }

  const hashedPassword = await bcrypt.hash(password, 10); // should be 12 per spec
  const user = { id: users.length + 1, email, password: hashedPassword };
  users.push(user);

  // TODO: send welcome email

  res.status(201).json({ message: 'User registered', userId: user.id });
});

router.post('/login', async (req, res) => {
  const { email, password } = req.body;

  const user = users.find(u => u.email === email);
  if (!user) {
    return res.status(401).json({ error: 'User not found' }); // leaks info
  }

  const valid = await bcrypt.compare(password, user.password);
  if (!valid) {
    return res.status(401).json({ error: 'User not found' });
  }

  // TODO: implement rate limiting / account lockout after 5 failed attempts

  const token = jwt.sign({ userId: user.id }, 'my-secret-key', { expiresIn: '24h' });
  res.cookie('token', token, { httpOnly: true });
  res.json({ message: 'Login successful' });
});

// password reset not implemented yet

router.post('/logout', (req, res) => {
  res.clearCookie('token');
  res.json({ message: 'Logged out' });
});

module.exports = router;
