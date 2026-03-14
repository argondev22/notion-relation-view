import { useState, useEffect } from "react";
import "./App.css";

function App() {
    const [status, setStatus] = useState<string>("Loading...");
    const [apiUrl] = useState(import.meta.env.VITE_API_URL || "http://localhost:8000");

    useEffect(() => {
        fetch(`${apiUrl}/health`)
            .then((res) => res.json())
            .then((data) => setStatus(data.status))
            .catch(() => setStatus("Error connecting to API"));
    }, [apiUrl]);

    return (
        <div className="App">
            <header className="App-header">
                <h1>Notion Relation View</h1>
                <p>Visualize your Notion connections</p>
                <p className="status">API Status: {status}</p>
            </header>
        </div>
    );
}

export default App;
