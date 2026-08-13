from __future__ import annotations
import networkx as nx
from .fco import FCO

class CustodyGraph:
    def __init__(self):
        self.g = nx.MultiDiGraph()

    def add_fco(self, fco: FCO):
        self.g.add_node(
            fco.digest,
            object_type=fco.object_type,
            claim=fco.claim,
            source=fco.source,
        )
        for parent in fco.parents:
            self.g.add_edge(parent, fco.digest, edge_type="DERIVED_TO")

    def add_relation(self, src: str, dst: str, edge_type: str, **attrs):
        self.g.add_edge(src, dst, edge_type=edge_type, **attrs)

    def to_node_link(self):
        return nx.node_link_data(self.g, edges="edges")
