import axios from "axios";

const api = axios.create({
    baseURL: "http://localhost:8000"
});

export interface Task {
    id: number;
    title: string;
    description: string;
    task_type: string;
    start_date: string | null;
    end_date: string | null;
    status: string;
}

interface ChatApiResponse {
    response: string;
}

export interface ChatResult {
    text: string;
    tasksFromReply: Task[];
}

function isTask(value: unknown): value is Task {
    if (typeof value !== "object" || value === null) {
        return false;
    }

    const candidate = value as Record<string, unknown>;

    return (
        typeof candidate.id === "number" &&
        typeof candidate.title === "string" &&
        typeof candidate.description === "string" &&
        typeof candidate.task_type === "string" &&
        (typeof candidate.start_date === "string" || candidate.start_date === null) &&
        (typeof candidate.end_date === "string" || candidate.end_date === null) &&
        typeof candidate.status === "string"
    );
}

function tryExtractTasksFromText(text: string): Task[] {
    const trimmed = text.trim();

    if (!trimmed) {
        return [];
    }

    try {
        const parsed = JSON.parse(trimmed) as unknown;

        if (Array.isArray(parsed)) {
            return parsed.filter(isTask);
        }

        if (isTask(parsed)) {
            return [parsed];
        }
    } catch {
        // Ignore non-JSON answer text.
    }

    const fencedJson = trimmed.match(/```json\s*([\s\S]*?)```/i);

    if (!fencedJson || fencedJson.length < 2) {
        return [];
    }

    try {
        const parsed = JSON.parse(fencedJson[1].trim()) as unknown;

        if (Array.isArray(parsed)) {
            return parsed.filter(isTask);
        }

        if (isTask(parsed)) {
            return [parsed];
        }
    } catch {
        return [];
    }

    return [];
}

export async function sendMessage(message: string): Promise<ChatResult> {

    const response = await api.post<ChatApiResponse>(
        "/chat",
        {
            message
        }
    );

    const text = response.data.response;

    return {
        text,
        tasksFromReply: tryExtractTasksFromText(text)
    };
}

export async function getTasks(): Promise<Task[]> {
    const response = await api.get<Task[]>("/tasks");

    if (!Array.isArray(response.data)) {
        return [];
    }

    return response.data.filter(isTask);
}