---
name: summarize-to-readme
description: Read a long text file and generate a clean, professional README.md with structured sections, tables, Mermaid diagrams, and key insights.
---

# README Generator

## Purpose

Use this skill whenever the user asks to:

- Summarize a long text file
- Convert documentation into a README
- Organize notes into documentation
- Create project documentation
- Produce a structured Markdown summary

The goal is to generate a polished, easy-to-read `README.md`.

---

# Instructions

## 1. Read the Entire Document

Read the entire input before generating any output.

Identify:

- Main topic
- Purpose
- Key concepts
- Important processes
- Relationships between ideas
- Conclusions
- Recommendations
- Metrics and numerical information (if present)

Never summarize only the beginning of the document.

---

## 2. Organize the Information

Arrange the content into clear logical sections.

Use the following structure when applicable:

# Project Title

Short description.

## Overview

## Objectives

## Key Concepts

## Workflow

## Architecture / Structure

## Features

## Important Findings

## Recommendations

## Frequently Asked Questions

## Summary

Skip sections that are not relevant.

---

## 3. Generate Visual Diagrams

When the source contains relationships, workflows, or architecture, create Mermaid diagrams.

Prefer:

- Flowcharts
- Mindmaps
- Sequence diagrams
- Entity Relationship diagrams
- State diagrams

Example Mermaid diagram:

flowchart TD
    A[Input File] --> B[Read Content]
    B --> C[Analyze]
    C --> D[Generate README]

Only generate diagrams that accurately represent the source.

Never invent workflows or architecture.

---

## 4. Use Tables

Whenever information fits naturally into a table, use Markdown tables.

Example:

| Section | Description |
|---------|-------------|
| Overview | General description |
| Workflow | Process summary |
| Findings | Important conclusions |

---

## 5. Highlight Key Insights

Create a section titled:

## Key Insights

Include between 5 and 10 concise bullet points describing the most important information from the document.

---

## 6. Summarize Metrics

If the document contains numbers, statistics, comparisons, dates, or measurements:

- Present them in Markdown tables.
- Preserve the original values.
- Do not invent missing data.

---

## 7. Improve Readability

The final README should be:

- Professional
- Well-structured
- Easy to scan
- Free from repetition
- Written in clear Markdown

Use:

- Headings
- Bullet lists
- Numbered lists
- Tables
- Code blocks (when appropriate)
- Mermaid diagrams (when appropriate)
- Callout blocks (`>`) for important notes

---

## 8. Output Rules

Return only the completed `README.md`.

Do not:

- Explain your reasoning.
- Mention the steps you followed.
- Comment on the quality of the source document.

The output must be a complete, polished Markdown document ready to save as `README.md`.