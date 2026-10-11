## What is RubriPDF

RubriPDF helps you assess with rubrics from start to finish. From a rubric and a list of students it generates, for each student, a PDF evaluation sheet that you grade comfortably on the computer; when you are done, the app collects all the marks into a single file.

The sections of this help follow the usual workflow: set up the document, define the criteria, add the students, generate the PDF, grade it and, finally, extract the marks.

## Set up the document

In this first part you define the header of the sheets. The **Subject** is the large heading on the cover, and the **Academic year** and the **Assessment title** form the subtitle.

The **Language** field sets the language in which the PDF is printed, which need not match the interface language (that one is changed at the top left). The **Header colour**, given as R,G,B values from 0 to 255, is the background on which each student's name appears.

## Define the criteria

Add as many criteria as you need, each with a description and its maximum points. With the buttons you can add or remove rows, and by dragging them from the left you change their order. The total points update on their own as you edit.

## Add the students

You can type the names by hand or import them from a file. RubriPDF recognises three sources and detects which one it is on its own:

- the **Secretaría Virtual** list (.xls),
- a **Moodle** participants export (.xlsx),
- any **plain list** (a .txt file or a single-column CSV, one name per line).

If something does not fit —columns it had to infer, duplicate names, or a file with several columns— it warns you at once. Names are kept exactly as they come, without touching them, so they match those of other systems. You can also drag them to reorder them.

## Output options

Before generating, you can add extra note pages per student (additional blank sheets for comments) and turn on **"Guide the notes with the rubric"**, which pre-fills each student's notes box with the numbered criteria, to comment point by point.

## Generate the PDF

Pressing **"Generate PDF"** gives you a document with one sheet per student. Each sheet has the criteria table, the final-mark field, an "Absent" checkbox and a space for notes, all as form fields you fill in directly on the computer (tested in Firefox and Chrome).

## Grade and extract the marks

Grade the PDF in a PDF reader, ticking the criteria and writing the marks. When you finish, upload it again in the extraction section and download the CSV with the marks.

During extraction a quality check runs that warns you of possible errors: unscored criteria, marks that are not numbers, sums that do not add up, values above the maximum, or students marked "Absent" that still have marks. If you left the final mark blank but scored the criteria, it is completed on its own with the sum.

The decimal separator and the CSV separator adapt to the language (comma and ";" in Galician, Spanish and Portuguese; dot and "," in English). If you tick **"Detailed CSV"**, the file also includes one column per criterion.

## Save and reuse the configuration

With the save and load buttons you can export the whole configuration —subject, criteria and options— to a JSON file and recover it whenever you want, for example for another assessment of the same subject. In addition, your work in progress is kept in the browser even if you close or reload the page.

## Privacy

RubriPDF runs entirely on your own computer: neither the students' names nor the marks are sent to any external server.
