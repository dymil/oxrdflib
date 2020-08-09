import unittest

from rdflib import RDF, Namespace, Graph, ConjunctiveGraph

EX = Namespace("http://example.com/")


class SparqlTestCase(unittest.TestCase):
    def test_ask_query(self):
        g = ConjunctiveGraph("OxMemory")
        g.add((EX.foo, RDF.type, EX.Entity))

        # basic
        result = g.query("ASK { ?s ?p ?o }")
        self.assertTrue(result)
        self.assertIsInstance(result.serialize(), bytes)

        # with init namespace
        self.assertTrue(g.query("ASK { ?s ?p ex:Entity }", initNs={"ex": EX}))

        # with init entities
        self.assertFalse(g.query("ASK { ?s ?p ?o }", initBindings={"o": EX.NotExists}))

        # in specific graph
        g = ConjunctiveGraph("OxMemory")
        g1 = Graph(store=g.store, identifier=EX.g1)
        g1.add((EX.foo, RDF.type, EX.Entity))
        self.assertTrue(g1.query("ASK { ?s ?p ?o }"))

    def test_select_query(self):
        g = ConjunctiveGraph("OxMemory")
        g.add((EX.foo, RDF.type, EX.Entity))
        result = g.query("SELECT * WHERE { ?s ?p ?o }")
        self.assertEquals(len(result), 1)
        self.assertIsInstance(result.serialize(), bytes)

    def test_construct_query(self):
        g = ConjunctiveGraph("OxMemory")
        g.add((EX.foo, RDF.type, EX.Entity))
        result = g.query("CONSTRUCT WHERE { ?s ?p ?o }")
        self.assertEquals(len(result), 1)
        self.assertIsInstance(result.serialize(), bytes)


if __name__ == "__main__":
    unittest.main()