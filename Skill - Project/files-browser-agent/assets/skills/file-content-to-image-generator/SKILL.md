---
name: file-to-image-generator
description: Read a document, analyze its content, create a detailed image prompt, generate an image URL using Pollinations AI, and return structured image data.
---

# File To Image Generator

## Purpose

Use this skill whenever the user asks to:

- Create an image based on a file
- Convert document content into a visual representation
- Generate an illustration from text
- Create a cover image from a document
- Visualize ideas, concepts, or information from a file
- Transform written content into an AI-generated image

The goal is to read the document, understand its meaning, create a suitable image prompt, generate an image URL, and return the image data.

---

# Instructions

## 1. Read the Entire Document

Always read the complete input file before generating an image.

Analyze:

- Main topic
- Purpose
- Key ideas
- Important objects
- People or characters
- Locations
- Actions
- Relationships between concepts
- Mood and atmosphere
- Visual elements
- Important symbols
- Numbers and important facts

Never generate an image based only on the beginning of the file.

---

## 2. Understand the Visual Intent

Determine what visual representation best matches the document.

Possible image types:

- Realistic scene
- Concept art
- Illustration
- Infographic
- Technical visualization
- Architecture diagram
- Poster
- Book cover
- 3D render
- Futuristic visualization
- Minimal professional design

Choose the style automatically based on the content.

---

## 3. Create an Image Prompt

Convert the document meaning into a detailed English image-generation prompt.

The prompt must contain:

- Main subject
- Environment
- Composition
- Visual hierarchy
- Lighting
- Color direction
- Artistic style
- Level of detail
- Camera perspective when relevant

Make the prompt optimized for AI image generation.

Example:

Input:

A project management system that connects teams and tracks tasks.

Output prompt:

A modern digital project management platform showing interconnected teams collaborating on tasks, central dashboard with charts and task cards, data flow visualization, professional futuristic technology environment, clean UI design, high detail, soft lighting.

---

## 4. Generate Image URL

After creating the prompt:

1. URL encode the complete prompt.
2. Create the image URL:

https://image.pollinations.ai/prompt/{encoded_prompt}

Example:

Prompt:

A futuristic city with robots

URL:

https://image.pollinations.ai/prompt/A%20futuristic%20city%20with%20robots

Always return a complete working URL.

---

## 5. Validate Result

Before returning:

Check:

- The prompt represents the document
- The URL was generated correctly
- Important context was included
- The visual style matches the source

---

## 6. Output Format

Return ONLY JSON.

Format:

{
  "title": "Generated Image",
  "image_url": "FULL_IMAGE_URL",
  "prompt": "IMAGE_PROMPT",
  "description": "SHORT_DESCRIPTION"
}

Example:

{
  "title": "Generated Image",
  "image_url": "https://image.pollinations.ai/prompt/A%20futuristic%20city%20with%20robots",
  "prompt": "A futuristic city with robots, cinematic lighting, highly detailed digital art",
  "description": "A futuristic technological city visualization."
}

---

## 7. Supported File Types

Support:

- TXT
- Markdown
- PDF
- DOCX
- HTML
- JSON
- CSV

Before processing:

- Extract meaningful text
- Remove metadata
- Ignore technical headers
- Remove duplicated content

---

## 8. Quality Rules

Generated images must be:

- Relevant to the source
- Professional
- Clear
- Visually meaningful
- Suitable for presentations or sharing

Avoid:

- Random decorative images
- Generic stock-style images
- Unrelated objects
- Information not supported by the document

---

## 9. Style Overrides

If the user specifies a style, follow it.

Examples:

- Realistic
- Futuristic
- Minimal
- Technical diagram
- Professional cover
- 3D render

The user's requested style overrides the default selection.

---

## 10. Error Handling

If the document does not contain enough visual information:

Create an image based on the main topic only.

If no file is provided:

Ask the user to upload a file.

Never return an empty image URL.