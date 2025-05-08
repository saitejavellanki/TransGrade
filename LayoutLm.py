id: The id of the document in Butler
tokens: The words in the document
bboxes: The bounding box for the corresponding word in tokens. Bounding boxes are in Min/Max format: [x_min, y_min, x_max, y_max]
ner_tags: The string form of the annotation for the corresponding word in tokens. Notice that we called as_ner with as_iob2=True so the annotations have been broken up into Inside-Outside-Beginning format.
image: A pillow image

https://medium.com/@matt.noe/tutorial-how-to-train-layoutlm-on-a-custom-dataset-with-hugging-face-cda58c96571c