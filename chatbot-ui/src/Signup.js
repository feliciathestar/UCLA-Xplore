import React, { useState, useContext } from "react";
import axios from "axios";
import { AuthContext } from "./AuthContext";
import { useNavigate, Link } from "react-router-dom";

const Signup = () => {
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: ""
  });
  const [error, setError] = useState("");

  const handleChange = (e) => 
    setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Change from '/auth/signup' to '/auth/register' to match your backend
      const res = await axios.post("http://localhost:8000/auth/register", formData);
      // If successful, store the token and redirect to chat
      login(res.data.access_token);
      navigate("/chat");
    } catch (err) {
      console.error("Registration error:", err.response?.data || err.message);
      setError(err.response?.data?.detail || "Registration failed. Please try a different username or email.");
    }
  };

  return (
    <div className="max-w-md mx-auto mt-8">
      <h2 className="text-2xl mb-4">Sign Up</h2>
      {error && <div className="text-red-500 mb-2">{error}</div>}
      <form onSubmit={handleSubmit}>
        <input
          name="username"
          value={formData.username}
          onChange={handleChange}
          placeholder="Username"
          className="border p-2 w-full mb-2"
          required
        />
        <input
          name="email"
          type="email"
          value={formData.email}
          onChange={handleChange}
          placeholder="Email"
          className="border p-2 w-full mb-2"
          required
        />
        <input
          name="password"
          type="password"
          value={formData.password}
          onChange={handleChange}
          placeholder="Password"
          className="border p-2 w-full mb-2"
          required
        />
        <button type="submit" className="bg-green-500 text-white px-4 py-2">
          Sign Up
        </button>
      </form>
      <p className="mt-4">
        Already have an account? <Link to="/login" className="text-blue-500 underline">Login here</Link>.
      </p>
    </div>
  );
};

export default Signup;
