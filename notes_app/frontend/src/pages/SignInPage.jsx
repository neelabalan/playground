import React, { useState } from "react";
import useAuth from "../hooks/useAuth";
import useFetchPrivate from "../hooks/useFetchPrivate";
import useNavigation from "../hooks/useNavigation";

const SignIn = () => {
  const [user, setUser] = useState("");
  const [pass, setPass] = useState("");
  const [error, setError] = useState("");
  const { setAuth } = useAuth();
  const fetchPrivate = useFetchPrivate();
  const { navigate } = useNavigation();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    const result = await fetchPrivate({
      method: "POST",
      endpoint: "/signin",
      body: { email: user, password: pass },
    });

    if (result.status === 200) {
      setAuth({
        accessToken: result.data.access_token,
        refreshToken: result.data.refresh_token,
        email: user,
      });
      navigate("/notes");
    } else {
      setError(result.data?.message || "Could not sign in");
    }
  };

  return (
    <>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={user}
          onChange={(e) => setUser(e.target.value)}
          placeholder="Email"
        />
        <input
          type="password"
          value={pass}
          onChange={(e) => setPass(e.target.value)}
          placeholder="Password"
        />
        {error && <p style={{ color: "red" }}>{error}</p>}
        <button type="submit">Sign In</button>
      </form>
    </>
  );
};

export default SignIn;