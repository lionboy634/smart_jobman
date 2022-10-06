from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
import os
import re
import pandas as pd
import numpy as np

#spacy
import spacy
from spacy.lang.en import stop_words
from spacy.pipeline import EntityRuler
from spacy.tokens import doc
from spacy.lang.en import English

import textract as tx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
# Create your views here.


#loads the spacy models once the server starts running
try:
    nlp = spacy.load('en_core_web_md')
    stopwords = stop_words.STOP_WORDS

#skill_pattern_path contains a list of skills that the entity ruler use to extract skills
    skill_pattern_path = "skills.jsonl"

#add entity ruler to nlp pipeline
    ruler = nlp.add_pipe("entity_ruler")
    ruler.from_disk(skill_pattern_path)
    #print(nlp.pipe_names)

except ImportError:
    print("Spacy's English Language Modules aren't present")

#handle the file uploads
def handle_uploaded_file(file, filename):
    if not os.path.exists('resume'):
        os.mkdir("resume")

    with open("resume/" + filename, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

#function convert text into tokens
def tokenize(text):
    text = re.sub(r'[^\w\s]', '', text)
    token = []
    doc = nlp(text)
    for tok in doc:
        token.append(str(tok))
    return token

#function removes stopwords from text
def remove_stopwords(text, stop=stopwords, optional_param=False, optional_words=[]):
    if optional_param:
        stop.append([a for a in optional_words ])
    return [word for word in text if word not in stop]

#function converts each words in its base form ex. running-> run is->be
def lemmatize(text):
    lemmatized = []
    sent = " ".join(text)
    doc = nlp(sent)
    for word in doc:
        lemmatized.append(word.lemma_)
    return lemmatized

#remove any part of speech except proper nouns nouns adverbs verbs and adjectives
def remove_tags(text, post_tags=["PROPN", "NOUN", "ADV", "VERB", "ADB"]):
    filtered = []
    str_text = nlp(" ".join(text))
    for token in str_text:
        if token.pos_ in post_tags:
            filtered.append(token.text)
    return filtered


#function returns a cleaned text after preprocessing the text
def _base_clean(text):
    text = tokenize(text)
    text = remove_stopwords(text)
    text = remove_tags(text)
    text = lemmatize(text)
    return text


#remove duplicated tokens or words
def _reduce_redundancy(text):
    #remove words that repeat themselves
    return set(list(text))


#Function targets the noun Part Of Speech(Noun) Proper nouns, commons nouns
def _get_target_words(text):
    target = []
    sent = " ".join(text)
    doc = nlp(sent)
    for token in doc:
        if token.tag_ in ["NN", "NNP"]:
            target.append(token.text)
    return target

def Cleaner(text):
    sent = []
    text = str(text)
    sent_cleaned = _base_clean(text)
    sent.append(sent_cleaned)
    sent_reduced = _reduce_redundancy(sent_cleaned)
    sent.append(sent_reduced)
    sent_targetted = _get_target_words(sent_reduced)
    sent.append(sent_targetted)
    return sent


resume_dir = "resume/"
resume_names = os.listdir(resume_dir)
def read_resume(list_of_resume, resume_directory):
    placeholder = []
    for res in list_of_resume:
        temp = []
        temp.append(res)
        text = tx.process(resume_directory+res, encoding='ascii')
        text = str(text, 'utf-8')
        temp.append(text)
        placeholder.append(temp)
    return placeholder


#function extracts skills from the resume
def extract_skills(text):
    doc = nlp(text)
    skills = []
    for ent in doc.ents:
        if ent.label_ == "SKILL":
            text = ent.text
            if text not in skills:
                skills.append(text)

    return skills





def tfidfvect(token):
    tfidf_vect = TfidfVectorizer(max_df=0.05, min_df=0.002)
    words = tfidf_vect.fit_transform(token)
    sentence = " ".join(tfidf_vect.get_feature_names())
    return sentence

def get_cleaned_words(document):
    for i in range(len(document)):
        raw = Cleaner(document[i][1])
        document[i].append(" ".join(raw[0]))
        document[i].append(" ".join(raw[1]))
        document[i].append(" ".join(raw[2]))
        sentence = tfidfvect(document[i][3].split(" "))
        document[i].append(sentence)
    return document



def match(resume, job_desc):
    score = cosine_similarity(resume, job_desc)
    return score * 100


def nlp_wrapper(text):
    return nlp(text)

    







        




