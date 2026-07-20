import { useEffect, useMemo, useState } from "react";
import {
    getTasks,
    sendMessage,
    type Task
} from "../services/chatService";

type Sender = "user" | "bot";

interface ChatMessage {
    id: number;
    sender: Sender;
    text: string;
}


function Chat() {

    const [messages, setMessages] = useState<ChatMessage[]>([
        {
            id: 1,
            sender: "bot",
            text: "שלום! אני יכול ליצור, לעדכן ולמחוק משימות. מה תרצה לעשות?"
        }
    ]);
    const [tasks, setTasks] = useState<Task[]>([]);
    const [isSending, setIsSending] = useState(false);
    const [isLoadingTasks, setIsLoadingTasks] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [input, setInput] = useState("");

    const sortedTasks = useMemo(
        () => [...tasks].sort((a, b) => b.id - a.id),
        [tasks]
    );

    async function refreshTasks() {
        try {
            setIsLoadingTasks(true);
            const latest = await getTasks();
            setTasks(latest);
            setError(null);
        } catch {
            setError("לא הצלחתי לטעון משימות מהשרת.");
        } finally {
            setIsLoadingTasks(false);
        }
    }

    useEffect(() => {
        void refreshTasks();
    }, []);

    async function handleSend() {

        const cleanInput = input.trim();

        if (!cleanInput || isSending) {
            return;
        }

        setIsSending(true);
        setError(null);

        const userMessage = {
            id: Date.now(),
            sender: "user",
            text: cleanInput
        };


        setMessages(prev => [
            ...prev,
            userMessage
        ]);

        setInput("");

        try {
            const answer = await sendMessage(cleanInput);

            setMessages(prev => [
                ...prev,
                {
                    id: Date.now() + 1,
                    sender: "bot",
                    text: answer.text
                }
            ]);

            if (answer.tasksFromReply.length > 0) {
                setTasks(answer.tasksFromReply);
            } else {
                await refreshTasks();
            }
        } catch {
            setError("הודעה לא נשלחה. בדוק שהשרת רץ על פורט 8000.");
        } finally {
            setIsSending(false);
        }
    }

    const statusClassName = (status: string) => {
        if (status.includes("בוצ")) return "done";
        if (status.includes("התקד")) return "progress";
        return "new";
    };

    return (
        <div className="dashboard-layout">
            <section className="chat-panel">
                <header className="panel-header">
                    <h1>Task Agent Console</h1>
                    <p>שלח פקודה חופשית והאייג'נט יעדכן את המשימות בזמן אמת.</p>
                </header>

                <div className="chat-log" aria-live="polite">
                    {messages.map((msg) => (
                        <article
                            key={msg.id}
                            className={`message-bubble ${msg.sender}`}
                        >
                            <span className="sender-chip">
                                {msg.sender === "user" ? "אתה" : "Agent"}
                            </span>
                            <p>{msg.text}</p>
                        </article>
                    ))}
                </div>

                {error && <p className="error-banner">{error}</p>}

                <div className="composer">
                    <input
                        value={input}
                        placeholder="למשל: צור משימת עבודה להגשת מצגת עד יום חמישי"
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter") {
                                void handleSend();
                            }
                        }}
                    />
                    <button onClick={() => void handleSend()} disabled={isSending}>
                        {isSending ? "שולח..." : "שלח"}
                    </button>
                </div>
            </section>

            <aside className="tasks-panel">
                <div className="tasks-title-row">
                    <h2>משימות</h2>
                    <button
                        className="ghost-btn"
                        onClick={() => void refreshTasks()}
                        disabled={isLoadingTasks}
                    >
                        רענן
                    </button>
                </div>

                {isLoadingTasks ? (
                    <p className="loading-text">טוען משימות...</p>
                ) : sortedTasks.length === 0 ? (
                    <p className="loading-text">עדיין אין משימות.</p>
                ) : (
                    <ul className="task-list">
                        {sortedTasks.map((task) => (
                            <li key={task.id} className="task-card">
                                <div className="task-head">
                                    <strong>{task.title}</strong>
                                    <span className={`status-pill ${statusClassName(task.status)}`}>
                                        {task.status}
                                    </span>
                                </div>
                                <p>{task.description}</p>
                                <div className="task-meta">
                                    <span>#{task.id}</span>
                                    <span>{task.task_type}</span>
                                    <span>
                                        {task.start_date ?? "-"} - {task.end_date ?? "-"}
                                    </span>
                                </div>
                            </li>
                        ))}
                    </ul>
                )}
            </aside>
        </div>
    );
}

export default Chat;