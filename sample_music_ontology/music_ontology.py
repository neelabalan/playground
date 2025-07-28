import pandas as pd
import rdflib
from rdflib.namespace import OWL
from rdflib.namespace import RDF
from rdflib.namespace import Namespace


def prepare_sample_data():
    df = pd.read_csv('dataset/tcc_ceds_music.csv')
    random_df = df.sample(n=200)
    selected_columns = ['artist_name', 'track_name', 'release_date', 'genre', 'topic']
    random_df = random_df[selected_columns]
    random_df.to_csv('dataset/sample_data.csv', index=False)


def fill_space_with_underscore(name):
    return name.lower().replace(' ', '_')


def create_ontology():
    g = rdflib.Graph()
    MUSIC = Namespace('https://example.org/ontology/music#')

    # classes and properties
    g.add((MUSIC.Artist, RDF.type, OWL.Class))
    g.add((MUSIC.Track, RDF.type, OWL.Class))
    g.add((MUSIC.Topic, RDF.type, OWL.Class))

    g.add((MUSIC.hasArtist, RDF.type, OWL.ObjectProperty))
    g.add((MUSIC.hasTopic, RDF.type, OWL.ObjectProperty))
    g.add((MUSIC.isArtistOf, RDF.type, OWL.ObjectProperty))
    g.add((MUSIC.isTopicOf, RDF.type, OWL.ObjectProperty))

    g.add((MUSIC.artistName, RDF.type, OWL.DatatypeProperty))
    g.add((MUSIC.trackName, RDF.type, OWL.DatatypeProperty))
    g.add((MUSIC.releaseDate, RDF.type, OWL.DatatypeProperty))
    g.add((MUSIC.genre, RDF.type, OWL.DatatypeProperty))
    g.add((MUSIC.topic, RDF.type, OWL.DatatypeProperty))

    data = pd.read_csv('dataset/sample_data.csv')

    # Populated the graph with data
    for i, row in data.iterrows():
        artist_uri = MUSIC[fill_space_with_underscore(row['artist_name'])]
        topic_uri = MUSIC[fill_space_with_underscore(row['topic'])]
        track_uri = MUSIC[fill_space_with_underscore(row['track_name'])]

        # Creating entities as instances of classes
        g.add((artist_uri, RDF.type, MUSIC.Artist))
        g.add((topic_uri, RDF.type, MUSIC.Topic))
        g.add((track_uri, RDF.type, MUSIC.Track))

        # Addding relationships
        g.add((track_uri, MUSIC.hasArtist, artist_uri))
        g.add((track_uri, MUSIC.hasTopic, topic_uri))
        g.add((artist_uri, MUSIC.isArtistOf, track_uri))
        g.add((topic_uri, MUSIC.isTopicOf, track_uri))

        # Adding literal values
        g.add((artist_uri, MUSIC.artistName, rdflib.Literal(row['artist_name'])))
        g.add((track_uri, MUSIC.trackName, rdflib.Literal(row['track_name'])))
        g.add((track_uri, MUSIC.releaseDate, rdflib.Literal(row['release_date'])))
        g.add((topic_uri, MUSIC.topic, rdflib.Literal(row['topic'])))
        g.add((track_uri, MUSIC.genre, rdflib.Literal(row['genre'])))

    g.serialize('music_ontology.ttl', format='turtle')


if __name__ == '__main__':
    prepare_sample_data()
    create_ontology()
