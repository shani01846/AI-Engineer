import axios from "axios";


const api = axios.create({
    baseURL: "http://localhost:8000"
});


interface ChatResponse {
    response: string;
}


export async function sendMessage(
    message: string
): Promise<string> {

    const response = await api.post<ChatResponse>(
        "/chat",
        {
            message
        }
    );

    return response.data.response;
}