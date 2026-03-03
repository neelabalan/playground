import React, { useState } from "react";
import useFetchPrivate from "../hooks/useFetchPrivate";
import useNavigation from "../hooks/useNavigation";

const SignUp = () => {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const fetchPrivate = useFetchPrivate();
  const { navigate } = useNavigation();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    const result = await fetchPrivate({
      method: "POST",
      endpoint: "/signup",
      body: { username, email, password },
    });

    if (result.status === 201) {
      setSuccess("Account created successfully! Redirecting to sign in...");
      setTimeout(() => navigate("/signin"), 1500);
    } else {
      setError(result.data?.message || "Could not create account");
    }
  };

  return (
    <>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
          required
        />
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          required
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          required
        />
        {error && <p style={{ color: "red" }}>{error}</p>}
        {success && <p style={{ color: "green" }}>{success}</p>}
        <button type="submit">Sign Up</button>
      </form>
    </>
  );
};

export default SignUp;
