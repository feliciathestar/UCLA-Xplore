import React, { useState, useContext } from "react";
import axios from "axios";
import { AuthContext } from "./AuthContext";

const Chat = () => {
  const { token } = useContext(AuthContext);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    try {
      const res = await axios.post(
        "http://localhost:8000/chat",
        { message: input },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      setMessages([
        ...messages,
        { sender: "user", text: input },
        { sender: "bot", text: res.data.response },
      ]);
      setInput("");
    } catch (error) {
      console.error("Error sending message", error);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="p-4 flex flex-col h-screen">
      <div className="flex-grow overflow-y-scroll mb-4">
        {messages.map((msg, idx) => (
          <div key={idx} className={`mb-2 ${msg.sender === "user" ? "text-right" : "text-left"}`}>
            <span className="inline-block p-2 rounded bg-gray-200">
              {msg.text}
            </span>
          </div>
        ))}
      </div>
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type your message..."
        className="border p-2 w-full"
        rows="2"
      />
      <button onClick={sendMessage} className="bg-blue-500 text-white px-4 py-2 mt-2 self-end">
        Send
      </button>
    </div>
  );
};

export default Chat;
