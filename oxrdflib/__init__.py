from abc import ABC, abstractmethod
import pyoxigraph as ox
from rdflib import Graph
from rdflib.store import Store, VALID_STORE
from rdflib.term import URIRef, BNode, Literal

__all__ = ["MemoryOxStore", "SledOxStore"]


class _BaseOxStore(Store, ABC):
    context_aware = True
    formula_aware = False
    transaction_aware = False
    graph_aware = False

    @property
    @abstractmethod
    def _inner(self):
        pass

    def gc(self):
        pass

    def add(self, triple, context, quoted=False):
        if quoted:
            raise ValueError("Oxigraph stores are not formula aware")
        self._inner.add(_to_ox(triple, context))
        super().add(triple, context, quoted)

    def remove(self, triple, context=None):
        for q in self._inner.quads_for_pattern(*_to_ox_quad_pattern(triple, context)):
            self._inner.remove(q)
        super().remove(triple, context)

    def triples(self, triple_pattern, context=None):
        return (_from_ox(q) for q in self._inner.quads_for_pattern(*_to_ox_quad_pattern(triple_pattern, context)))

    def __len__(self, context=None):
        if context is None:
            # TODO: very bad
            return len({q.triple for q in self._inner})
        else:
            return sum(1 for _ in self._inner.quads_for_pattern(None, None, None, _to_ox(context)))

    def contexts(self, triple=None):
        iter = self._inner if triple is None else self._inner.quads_for_pattern(*_to_ox_quad_pattern(triple))
        return (_from_ox(q[3]) for q in iter)

    def query(self, query, initNs, initBindings, queryGraph, **kwargs):
        raise NotImplementedError

    def update(self, update, initNs, initBindings, queryGraph, **kwargs):
        raise NotImplementedError

    def commit(self):
        """ TODO: implement """

    def rollback(self):
        """ TODO: implement """


class MemoryOxStore(_BaseOxStore):
    def __init__(self, configuration=None, identifier=None):
        self._store = ox.MemoryStore()
        super().__init__(configuration, identifier)

    @property
    def _inner(self):
        return self._store


class SledOxStore(_BaseOxStore):
    def __init__(self, configuration=None, identifier=None):
        self._store = None
        super().__init__(configuration, identifier)

    def open(self, configuration, create=False):
        self._store = ox.SledStore(configuration)
        return VALID_STORE

    def close(self, commit_pending_transaction=False):
        del self._store

    def destroy(self, configuration):
        raise NotImplementedError("destroy is not implemented yet for the Sled based store")

    @property
    def _inner(self):
        if self._store is None:
            self._store = ox.SledStore()
        return self._store


def _to_ox(term, context=None):
    if term is None:
        return None
    elif isinstance(term, URIRef):
        return ox.NamedNode(term)
    elif isinstance(term, BNode):
        return ox.BlankNode(term)
    elif isinstance(term, Literal):
        return ox.Literal(term, language=term.language, datatype=ox.NamedNode(term.datatype) if term.datatype else None)
    elif isinstance(term, Graph):
        return _to_ox(term.identifier)
    elif isinstance(term, tuple):
        if len(term) == 3:
            return ox.Quad(_to_ox(term[0]), _to_ox(term[1]), _to_ox(term[2]), _to_ox(context))
        elif len(term) == 4:
            return ox.Quad(_to_ox(term[0]), _to_ox(term[1]), _to_ox(term[2]), _to_ox(term[3]))
        else:
            raise ValueError("Unexpected rdflib term: {}".format(repr(term)))
    else:
        raise ValueError("Unexpected rdflib term: {}".format(repr(term)))


def _to_ox_quad_pattern(triple, context=None):
    (s, p, o) = triple
    return _to_ox_term_pattern(s), _to_ox_term_pattern(p), _to_ox_term_pattern(o), _to_ox_term_pattern(context)


def _to_ox_term_pattern(term):
    if term is None:
        return None
    elif isinstance(term, URIRef):
        return ox.NamedNode(term)
    elif isinstance(term, BNode):
        return ox.BlankNode(term)
    elif isinstance(term, Literal):
        return ox.Literal(term, language=term.language, datatype=ox.NamedNode(term.datatype) if term.datatype else None)
    elif isinstance(term, Graph):
        return _to_ox(term.identifier)
    else:
        raise ValueError("Unexpected rdflib term: {}".format(repr(term)))


def _from_ox(term):
    if isinstance(term, ox.NamedNode):
        return URIRef(term.value)
    elif isinstance(term, ox.BlankNode):
        return BNode(term.value)
    elif isinstance(term, ox.Literal):
        return Literal(term.value, lang=term.language, datatype=URIRef(term.datatype.value))
    elif isinstance(term, ox.DefaultGraph):
        return None
    elif isinstance(term, ox.Triple):
        return _from_ox(term.subject), _from_ox(term.predicate), _from_ox(term.object)
    elif isinstance(term, ox.Quad):
        return (_from_ox(term.subject), _from_ox(term.predicate), _from_ox(term.object)), _from_ox(term.graph_name)
    else:
        raise ValueError("Unexpected Oxigraph term: {}".format(repr(term)))