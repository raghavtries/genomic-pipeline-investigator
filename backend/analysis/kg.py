"""
Knowledge graph construction for genomics pipeline runs.
Builds networkx graph and exports to vis-network format.
"""
import networkx as nx
import json
import hashlib
from typing import Dict, List, Any
from pathlib import Path
import datetime

class KnowledgeGraph:
    """Builds knowledge graphs for genomics pipeline runs."""
    
    def __init__(self):
        self.graph = nx.DiGraph()
    
    def add_run_node(self, run_id: str, metadata: Dict[str, Any] = None):
        """Add a run node to the graph."""
        self.graph.add_node(
            f"run_{run_id}",
            type="Run",
            run_id=run_id,
            timestamp=datetime.datetime.now().isoformat(),
            metadata=metadata or {}
        )
    
    def add_reference_node(self, ref_path: str, build: str = None):
        """Add a reference genome node."""
        ref_hash = self._get_file_hash(ref_path)
        node_id = f"ref_{ref_hash[:8]}"
        
        self.graph.add_node(
            node_id,
            type="Reference",
            build=build,
            hash=ref_hash,
            path=ref_path
        )
        return node_id
    
    def add_aligner_node(self, tag: str, version: str = None):
        """Add an aligner node."""
        node_id = f"aligner_{tag}"
        self.graph.add_node(
            node_id,
            type="Aligner",
            tag=tag,
            version=version
        )
        return node_id
    
    def add_caller_node(self, tag: str, version: str = None):
        """Add a variant caller node."""
        node_id = f"caller_{tag}"
        self.graph.add_node(
            node_id,
            type="Caller",
            tag=tag,
            version=version
        )
        return node_id
    
    def add_vcf_node(self, vcf_path: str):
        """Add a VCF file node."""
        vcf_hash = self._get_file_hash(vcf_path)
        node_id = f"vcf_{vcf_hash[:8]}"
        
        self.graph.add_node(
            node_id,
            type="VCF",
            hash=vcf_hash,
            path=vcf_path
        )
        return node_id
    
    def add_annotator_node(self, tool: str, db_version: str):
        """Add an annotation tool node."""
        node_id = f"annotator_{tool}_{db_version}"
        self.graph.add_node(
            node_id,
            type="Annotator",
            tool=tool,
            db_version=db_version
        )
        return node_id
    
    def add_db_version_node(self, db_id: str, version: str):
        """Add a database version node."""
        node_id = f"db_{db_id}_{version}"
        self.graph.add_node(
            node_id,
            type="DBVersion",
            id=db_id,
            version=version
        )
        return node_id
    
    def add_predictor_node(self, model_path: str, model_name: str = None):
        """Add a prediction model node."""
        model_hash = self._get_file_hash(model_path)
        node_id = f"predictor_{model_hash[:8]}"
        
        self.graph.add_node(
            node_id,
            type="Predictor",
            model=model_name or "unknown",
            hash=model_hash,
            path=model_path
        )
        return node_id
    
    def add_output_node(self, output_path: str, output_type: str):
        """Add an output node."""
        output_hash = self._get_file_hash(output_path)
        node_id = f"output_{output_hash[:8]}"
        
        self.graph.add_node(
            node_id,
            type="Output",
            output_type=output_type,
            hash=output_hash,
            path=output_path
        )
        return node_id
    
    def add_edge(self, source: str, target: str, edge_type: str, metadata: Dict[str, Any] = None):
        """Add an edge between nodes."""
        self.graph.add_edge(
            source, target,
            type=edge_type,
            metadata=metadata or {}
        )
    
    def attach_metrics(self, node_id: str, metrics: Dict[str, Any]):
        """Attach metrics to a node."""
        if node_id in self.graph:
            self.graph.nodes[node_id]["metrics"] = metrics
    
    def _get_file_hash(self, file_path: str) -> str:
        """Get SHA256 hash of a file."""
        if not Path(file_path).exists():
            return "missing"
        
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    def to_vis_network(self) -> Dict[str, List[Dict[str, Any]]]:
        """Convert to vis-network format."""
        nodes = []
        edges = []
        
        for node_id, data in self.graph.nodes(data=True):
            # Create vis-network node
            vis_node = {
                "id": node_id,
                "label": self._get_node_label(node_id, data),
                "group": data.get("type", "unknown"),
                "title": self._get_node_title(data)
            }
            
            # Add color based on type
            vis_node["color"] = self._get_node_color(data.get("type"))
            
            nodes.append(vis_node)
        
        for source, target, data in self.graph.edges(data=True):
            # Create vis-network edge
            vis_edge = {
                "from": source,
                "to": target,
                "label": data.get("type", ""),
                "arrows": "to"
            }
            
            # Add color based on edge type
            vis_edge["color"] = self._get_edge_color(data.get("type"))
            
            edges.append(vis_edge)
        
        return {"nodes": nodes, "edges": edges}
    
    def _get_node_label(self, node_id: str, data: Dict[str, Any]) -> str:
        """Get label for vis-network node."""
        node_type = data.get("type", "unknown")
        
        if node_type == "Run":
            return f"Run {data.get('run_id', '')}"
        elif node_type == "Reference":
            return f"Ref {data.get('build', '')}"
        elif node_type == "Aligner":
            return f"Align {data.get('tag', '')}"
        elif node_type == "Caller":
            return f"Call {data.get('tag', '')}"
        elif node_type == "VCF":
            return f"VCF {node_id[-8:]}"
        elif node_type == "Annotator":
            return f"Annot {data.get('tool', '')}"
        elif node_type == "DBVersion":
            return f"DB {data.get('version', '')}"
        elif node_type == "Predictor":
            return f"Model {data.get('model', '')}"
        elif node_type == "Output":
            return f"Out {data.get('output_type', '')}"
        
        return node_id
    
    def _get_node_title(self, data: Dict[str, Any]) -> str:
        """Get title (tooltip) for vis-network node."""
        title_parts = []
        
        for key, value in data.items():
            if key not in ["type", "metrics"]:
                title_parts.append(f"{key}: {value}")
        
        if "metrics" in data:
            title_parts.append(f"Metrics: {len(data['metrics'])} items")
        
        return "\\n".join(title_parts)
    
    def _get_node_color(self, node_type: str) -> str:
        """Get color for vis-network node based on type."""
        colors = {
            "Run": "#FF6B6B",
            "Reference": "#4ECDC4", 
            "Aligner": "#45B7D1",
            "Caller": "#96CEB4",
            "VCF": "#FFEAA7",
            "Annotator": "#DDA0DD",
            "DBVersion": "#98D8C8",
            "Predictor": "#F7DC6F",
            "Output": "#BB8FCE"
        }
        return colors.get(node_type, "#95A5A6")
    
    def _get_edge_color(self, edge_type: str) -> str:
        """Get color for vis-network edge based on type."""
        colors = {
            "uses": "#3498DB",
            "produced_by": "#E74C3C",
            "depends_on": "#F39C12"
        }
        return colors.get(edge_type, "#95A5A6")
    
    def save_graph(self, run_id: str, output_dir: str):
        """Save graph in multiple formats."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create a clean graph without None values for GML export
        clean_graph = nx.DiGraph()
        for node_id, data in self.graph.nodes(data=True):
            clean_data = {k: v for k, v in data.items() if v is not None}
            clean_graph.add_node(node_id, **clean_data)
        
        for source, target, data in self.graph.edges(data=True):
            clean_data = {k: v for k, v in data.items() if v is not None}
            clean_graph.add_edge(source, target, **clean_data)
        
        # Save networkx graph
        nx.write_gml(clean_graph, output_path / "kg.gml")
        
        # Save vis-network JSON
        vis_data = self.to_vis_network()
        with open(output_path / "kg.json", 'w') as f:
            json.dump(vis_data, f, indent=2)
        
        return str(output_path / "kg.json")