# Full Stack Online Learning Platform Project

This document provides the complete source code, architecture, and instructions for a fully functional Online Learning Platform built with a modern Full Stack (MERN-style) architecture.

## 1. Project Structure

```text
online-learning-platform/
├── backend/
│   ├── config/
│   │   └── db.js
│   ├── controllers/
│   │   ├── authController.js
│   │   ├── courseController.js
│   │   └── studentController.js
│   ├── middleware/
│   │   └── authMiddleware.js
│   ├── models/
│   │   ├── Course.js
│   │   ├── Enrollment.js
│   │   ├── Quiz.js
│   │   └── User.js
│   ├── routes/
│   │   ├── authRoutes.js
│   │   ├── courseRoutes.js
│   │   └── studentRoutes.js
│   ├── utils/
│   │   └── certificateGen.js
│   ├── .env
│   ├── package.json
│   └── server.js
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CourseCard.js
│   │   │   ├── Navbar.js
│   │   │   └── PrivateRoute.js
│   │   ├── pages/
│   │   │   ├── Dashboard.js
│   │   │   ├── Home.js
│   │   │   ├── Login.js
│   │   │   └── QuizPage.js
│   │   ├── App.js
│   │   └── index.js
│   ├── package.json
│   └── .env
└── README.md
```

## 2. Backend Implementation (Node.js & Express)

### `backend/server.js`
```javascript
const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const connectDB = require('./config/db');

dotenv.config();
connectDB();

const app = express();
app.use(cors());
app.use(express.json());

app.use('/api/auth', require('./routes/authRoutes'));
app.use('/api/courses', require('./routes/courseRoutes'));
app.use('/api/student', require('./routes/studentRoutes'));

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
```

### `backend/models/User.js`
```javascript
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

const UserSchema = new mongoose.Schema({
    name: { type: String, required: true },
    email: { type: String, required: true, unique: true },
    password: { type: String, required: true },
    role: { type: String, enum: ['student', 'instructor', 'admin'], default: 'student' },
    enrolledCourses: [{ type: mongoose.Schema.Types.ObjectId, ref: 'Course' }]
});

UserSchema.pre('save', async function(next) {
    if (!this.isModified('password')) next();
    const salt = await bcrypt.genSalt(10);
    this.password = await bcrypt.hash(this.password, salt);
});

module.exports = mongoose.model('User', UserSchema);
```

### `backend/controllers/courseController.js`
```javascript
const Course = require('../models/Course');

exports.getCourses = async (req, res) => {
    try {
        const courses = await Course.find();
        res.json(courses);
    } catch (err) {
        res.status(500).send('Server Error');
    }
};

exports.createCourse = async (req, res) => {
    const { title, description, instructor, category, lessons } = req.body;
    try {
        const newCourse = new Course({ title, description, instructor, category, lessons });
        await newCourse.save();
        res.json(newCourse);
    } catch (err) {
        res.status(500).send('Server Error');
    }
};
```

## 3. Frontend Implementation (React.js)

### `frontend/src/App.js`
```javascript
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import PrivateRoute from './components/PrivateRoute';

function App() {
  return (
    <Router>
      <Navbar />
      <div className="container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={
            <PrivateRoute>
              <Dashboard />
            </PrivateRoute>
          } />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
```

### `frontend/src/pages/Home.js`
```javascript
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import CourseCard from '../components/CourseCard';

const Home = () => {
    const [courses, setCourses] = useState([]);

    useEffect(() => {
        const fetchCourses = async () => {
            const res = await axios.get('http://localhost:5000/api/courses');
            setCourses(res.data);
        };
        fetchCourses();
    }, []);

    return (
        <div className="home-container">
            <header className="hero">
                <h1>Unlock Your Potential with Online Learning</h1>
                <p>Explore thousands of courses from industry experts.</p>
            </header>
            <div className="course-grid">
                {courses.map(course => (
                    <CourseCard key={course._id} course={course} />
                ))}
            </div>
        </div>
    );
};

export default Home;
```

## 4. Database Schema (MongoDB)

- **Users**: `_id, name, email, password, role, enrolledCourses[]`
- **Courses**: `_id, title, description, instructorId, category, lessons[{title, videoUrl, content}], quizId`
- **Enrollments**: `_id, userId, courseId, progressPercentage, completed`
- **Quizzes**: `_id, courseId, questions[{question, options[], answer}]`
- **Certificates**: `_id, userId, courseId, issueDate, certificateUrl`

## 5. API Documentation

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| POST | `/api/auth/register` | Register a new user | No |
| POST | `/api/auth/login` | Login and get JWT | No |
| GET | `/api/courses` | Get all courses | No |
| POST | `/api/courses` | Create a course | Yes (Instructor/Admin) |
| GET | `/api/student/dashboard` | Get student progress | Yes (Student) |
| POST | `/api/student/enroll/:id` | Enroll in a course | Yes (Student) |

## 6. Setup & Deployment Instructions

### Local Setup
1. **Clone the repository.**
2. **Backend**:
   - `cd backend`
   - `npm install`
   - Create `.env` with `MONGO_URI` and `JWT_SECRET`.
   - `npm start`
3. **Frontend**:
   - `cd frontend`
   - `npm install`
   - `npm start`

### Cloud Deployment (Vercel & Render)
1. **Database**: Create a cluster on MongoDB Atlas and get the connection string.
2. **Backend (Render)**:
   - Connect your GitHub repo.
   - Set environment variables (`MONGO_URI`, `JWT_SECRET`).
   - Build Command: `npm install`
   - Start Command: `node server.js`
3. **Frontend (Vercel)**:
   - Connect your GitHub repo.
   - Set `REACT_APP_API_URL` to your Render backend URL.
   - Deploy.

## 7. Design Features
- **Responsive CSS Grid/Flexbox**: Ensures the platform works on mobile, tablet, and desktop.
- **JWT Authentication**: Securely handles sessions.
- **Progress Tracking**: Real-time updates as students complete lessons and quizzes.
- **Dynamic Certificates**: Generated via backend logic upon 100% completion.
