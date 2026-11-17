<!-- Source: RAG_Chatbot_Assignment_Technical.docx (course assignment brief), converted to Markdown. -->

EVALUATION DOCUMENT

# RAG-Based Chatbot Assignment

Technical implementation track

GROUP ASSIGNMENT: Work in groups of 4–5 students. Each group will present its chatbot in a strict 5-minute slot: problem statement, 3–4-minute demo, and 1–2-minute Q&A. No extra time will be provided.

# 1. Problem statement

Build a Retrieval-Augmented Generation (RAG) chatbot that helps users find reliable, relevant answers from a selected company’s product, service, policy, or knowledge dataset. For example, a fashion chatbot could answer questions about products, fabric, fit, price, availability, care instructions, and returns using a Myntra-style catalogue. Your chatbot must ground its answers in retrieved data rather than relying only on the language model’s general knowledge.

# 2. Choose your use case

Select one industry and a company within it. Define a realistic user and a clear purpose for the chatbot—for example, product discovery, policy Q&A, service comparison, troubleshooting, or customer support.

# Suggested industries and company examples

Choose one industry and one company, or select another suitable company. These are starting points, not a restricted list.

| Industry | Example companies |
|---|---|
| Fashion & Apparel | Myntra, Zara, H&M |
| Beauty & Personal Care | Nykaa, Sephora, The Body Shop |
| Consumer Electronics | Croma, Reliance Digital, Apple |
| Travel & Hospitality | MakeMyTrip, Airbnb, Marriott |
| Food & Grocery | BigBasket, Blinkit, Swiggy Instamart |
| Automotive | Tata Motors, Hyundai, Maruti Suzuki |
| Banking & Financial Services | HDFC Bank, ICICI Bank, Zerodha |
| Healthcare & Pharmacy | Apollo Pharmacy, Tata 1mg, Practo |
| Education & Online Learning | Coursera, upGrad, Udemy |

Other possible areas include telecom, real estate, logistics, insurance, sports and fitness, home furnishings, and quick commerce.

# 3. Dataset requirements

- Find a suitable dataset on Kaggle or another credible public source. You may also use publicly available company/product information where permitted.

- The dataset must contain a meaningful description column for each product, service, policy, item, or record. The description should contain enough natural-language detail to retrieve useful context.

- Useful fields may include item/product name, category, brand/company, price, features, specifications, target user, FAQs, policy details, or other attributes relevant to the use case.

- Clean the data and remove duplicate, empty, or clearly irrelevant records. Keep track of the source and any assumptions.

- If you cannot find a suitable dataset, create a realistic synthetic dataset with ChatGPT. Include at least 50 records, with a description column, and review the generated data for consistency. Clearly label it as synthetic.

- Aim for enough content to demonstrate meaningful retrieval. A dataset with only a handful of short rows may not be sufficient.

# 4. What you need to build

- Prepare and load the dataset/documents for retrieval.

- Apply a chunking strategy where appropriate. Explain your choice of chunk size, overlap, and/or document structure.

- Generate embeddings and store them in a vector store.

- Implement retrieval to fetch relevant chunks for a user query.

- Pass the retrieved context and user question to an LLM to generate a grounded answer.

- Build a simple **Streamlit** user interface with a chat input and visible responses. A plain, functional UI is sufficient; a custom frontend is not required.

- Add a fallback for questions that are not supported by the dataset. The chatbot should say when the available context is insufficient instead of inventing an answer.

- Include a short explanation of your pipeline: data → chunking → embeddings → vector store → retrieval → LLM/context → answer.

# 5. RAG techniques

Core requirement: implement a working baseline RAG pipeline. (Mandatory)

Optional:

Enhancement requirement: implement **at least one** of the following, if covered in your course and feasible within the assignment:

- Hybrid RAG: combine semantic/vector retrieval with keyword-based retrieval, then merge or rank the results.

- Query decomposition RAG: break a complex question into smaller sub-questions, retrieve evidence for each, and combine the evidence into a final answer.

# 6. Test and evaluate

- Prepare at least 3-4 test questions: factual lookups, comparison questions, multi-part questions, and questions whose answers are not in the dataset.

- Check whether the retrieved chunks actually contain evidence needed to answer each question.

- Evaluate answer correctness, relevance, faithfulness to retrieved context, and appropriate handling of unsupported questions.

- Document at least two failure cases and explain how you would improve chunking, retrieval, metadata, prompts, or the dataset.

# 7. Deliverables

- Working Streamlit RAG chatbot, similar to what we covered in class

- Live Presentation- 5 mins each group

# 8. Suggested assessment rubric

| Assessment criterion | Weight |
|---|---|
| Problem definition and dataset quality | 15% |
| RAG pipeline: chunking, embeddings, vector store, retrieval, generation | 50% |
| Grounded answers and handling unsupported questions | 15% |
| Streamlit UI and usability | 10% |
| Testing, evaluation, and error analysis | 10% |

# Group formation and presentation (mandatory)

Group size: Students must work in groups of 4–5. Each group must build and present a RAG-based chatbot for the industry and company selected for its assignment.

Strict time limit: Each group has exactly 5 minutes. No extra time will be provided. Groups must finish within the allotted time.

Presentation structure (5 minutes total):

- Problem statement (approximately 1 minute): Explain the company, its industry, the target users, and the specific problem you are solving using RAG.

- Chatbot demonstration (3–4 minutes): Demonstrate the working chatbot and show how it retrieves relevant information and answers representative questions.

- Q&A (1–2 minutes): Answer questions about the problem, dataset, design choices, and chatbot behaviour.

Time management: The timings above are guidance for a concise presentation and must fit within the 5-minute total. Plan and rehearse in advance. The presentation will be stopped at the 5-minute mark, and no extension will be given.

