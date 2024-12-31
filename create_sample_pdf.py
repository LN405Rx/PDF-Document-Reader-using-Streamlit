from fpdf import FPDF
import os

# Create pdf_books directory if it doesn't exist
if not os.path.exists('pdf_books'):
    os.makedirs('pdf_books')

# Create PDF object
pdf = FPDF()

# Add a page
pdf.add_page()

# Set font
pdf.set_font("Arial", size=12)

# Add some sample text
sample_text = """Welcome to the PDF to Audiobook Converter!

This is a sample PDF document created to test the PDF to Audiobook conversion application. 

Chapter 1: The Power of the Human Brain

The human brain is remarkably adaptable. Scientists call this trait "neuroplasticity." It means our brains can form new neural connections throughout our lives, helping us learn new skills and adapt to new situations. Recent studies have shown that even in adulthood, our brains continue to create new neural pathways and modify existing ones to adapt to new experiences, learn new information, and create new memories.

The concept of neuroplasticity has revolutionized our understanding of brain development and learning. Previously, scientists believed that the brain's structure was relatively fixed after childhood. However, modern research has demonstrated that the brain continues to reorganize itself by forming new neural connections throughout life. This ability to adapt and change is what allows us to learn new skills, recover from brain injuries, and strengthen certain cognitive functions through training and experience.

Chapter 2: The Science of Learning

Reading and listening are two different ways we process information. When we read, we use our visual cortex to process written words. When we listen, we engage our auditory cortex to process spoken words. Both methods can be equally effective for learning and understanding information.

Research has shown that combining multiple learning methods can enhance comprehension and retention. This is known as multimodal learning. When we engage both visual and auditory processing centers, we create stronger neural connections and improve our ability to recall information later.

Chapter 3: The Digital Age of Learning

In today's digital age, we have access to various tools and technologies that can enhance our learning experience. Audiobooks, in particular, have gained popularity for several reasons:

1. Accessibility: They make literature accessible to people with visual impairments or reading difficulties.
2. Multitasking: Listeners can engage with books while doing other activities.
3. Pronunciation: They help learners understand correct pronunciation, especially for language learning.
4. Emotional Connection: Professional narration can add emotional depth to the content.
5. Time Efficiency: People can consume content while commuting or doing other tasks.

Chapter 4: The Future of Learning

As technology continues to advance, we're seeing new innovations in how we consume and process information:

- Artificial Intelligence is making text-to-speech more natural and expressive
- Virtual Reality is creating immersive learning environments
- Augmented Reality is blending digital and physical learning spaces
- Adaptive Learning Systems are personalizing education
- Brain-Computer Interfaces are opening new possibilities for direct neural learning

This sample text demonstrates various features of text-to-speech conversion, including:
- Handling of paragraphs and chapters
- Processing of punctuation
- Voice modulation for different types of sentences
- Proper pacing and natural flow
- Handling of lists and structured content
- Processing of technical terms and concepts

The advancement of text-to-speech technology has made it possible to convert written content into natural-sounding speech with proper intonation, rhythm, and emphasis. This technology continues to improve, making the listening experience more engaging and natural.

Some key benefits of using text-to-speech technology include:

1. Improved Accessibility
   - Helps people with visual impairments
   - Assists those with reading difficulties
   - Makes content available in audio format

2. Enhanced Learning
   - Supports different learning styles
   - Helps with pronunciation
   - Improves comprehension

3. Increased Productivity
   - Enables multitasking
   - Saves time
   - Reduces eye strain

Feel free to use this sample document to test the various features of the PDF to Audiobook converter. You can adjust the reading speed, volume, and voice settings to find your preferred combination.

Remember that everyone has different preferences when it comes to listening to audiobooks. Some prefer faster speeds for quick consumption, while others prefer slower speeds for better comprehension. The beauty of digital audio is that you can customize the experience to suit your needs.

Thank you for using our application! We hope this sample document helps you explore and understand the capabilities of our PDF to Audiobook converter.

Note: This sample document contains various types of content to help you test different aspects of the text-to-speech conversion, including regular paragraphs, lists, technical terms, and different punctuation marks."""

# Add text to PDF
pdf.multi_cell(0, 10, sample_text)

# Save the PDF
pdf.output("pdf_books/sample.pdf")
