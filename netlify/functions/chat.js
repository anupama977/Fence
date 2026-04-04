import OpenAI from "openai";

export async function handler(event) {
  const { message } = JSON.parse(event.body);

  const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
  });

  const response = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [
      {
        role: "system",
        content: `
You are a help assistant for Fence Pink Panthers website.

- Help users understand the app
- Guide them through features
- Keep answers short and clear
        `
      },
      {
        role: "user",
        content: message
      }
    ]
  });

  return {
    statusCode: 200,
    body: JSON.stringify({
      reply: response.choices[0].message.content
    })
  };
}
