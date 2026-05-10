#!/usr/bin/env python3
"""Generate test fixtures and SVGs for all supported template types."""
import json, os, subprocess

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
SCRIPT = os.path.join(os.path.dirname(__file__), "generate-from-template.py")
PREVIEW_SCRIPT = os.path.join(os.path.dirname(__file__), "build-preview.py")

fixtures = {
    "data-flow-style1": {
        "template_type": "data-flow", "style": 1,
        "width": 960, "height": 600,
        "title": "Data Pipeline", "subtitle": "ETL data flow diagram",
        "nodes": [
            {"id": "src", "kind": "cylinder", "x": 80, "y": 200, "width": 140, "height": 90, "label": "Source DB"},
            {"id": "extract", "kind": "rect", "x": 300, "y": 210, "width": 150, "height": 60, "label": "Extract"},
            {"id": "transform", "kind": "rect", "x": 530, "y": 210, "width": 150, "height": 60, "label": "Transform"},
            {"id": "load", "kind": "rect", "x": 740, "y": 210, "width": 150, "height": 60, "label": "Load"},
            {"id": "dw", "kind": "cylinder", "x": 760, "y": 370, "width": 140, "height": 90, "label": "Data Warehouse"},
            {"id": "api", "kind": "rect", "x": 80, "y": 400, "width": 140, "height": 50, "label": "REST API"},
            {"id": "queue", "kind": "double_rect", "x": 300, "y": 390, "width": 150, "height": 70, "label": "Message Queue"}
        ],
        "arrows": [
            {"source": "src", "target": "extract", "source_port": "right", "target_port": "left", "flow": "read"},
            {"source": "extract", "target": "transform", "source_port": "right", "target_port": "left", "flow": "control"},
            {"source": "transform", "target": "load", "source_port": "right", "target_port": "left", "flow": "write"},
            {"source": "load", "target": "dw", "source_port": "bottom", "target_port": "top", "flow": "data"},
            {"source": "api", "target": "queue", "source_port": "right", "target_port": "left", "flow": "control"},
            {"source": "queue", "target": "transform", "source_port": "top", "target_port": "bottom", "flow": "read"}
        ]
    },
    "flowchart-style1": {
        "template_type": "flowchart", "style": 1,
        "width": 960, "height": 640,
        "title": "User Registration Flow", "subtitle": "Decision flowchart",
        "nodes": [
            {"id": "start", "kind": "stadium", "x": 380, "y": 60, "width": 160, "height": 50, "label": "Start"},
            {"id": "input", "kind": "parallelogram", "x": 370, "y": 160, "width": 180, "height": 55, "label": "User Input"},
            {"id": "valid", "kind": "diamond", "x": 380, "y": 270, "width": 170, "height": 100, "label": "Valid?"},
            {"id": "create", "kind": "rect", "x": 380, "y": 430, "width": 160, "height": 55, "label": "Create Account"},
            {"id": "error", "kind": "rect", "x": 650, "y": 280, "width": 160, "height": 55, "label": "Show Error"},
            {"id": "end", "kind": "stadium", "x": 380, "y": 540, "width": 160, "height": 50, "label": "End"}
        ],
        "arrows": [
            {"source": "start", "target": "input", "source_port": "bottom", "target_port": "top", "flow": "control"},
            {"source": "input", "target": "valid", "source_port": "bottom", "target_port": "top", "flow": "control"},
            {"source": "valid", "target": "create", "source_port": "bottom", "target_port": "top", "flow": "control", "label": "Yes"},
            {"source": "valid", "target": "error", "source_port": "right", "target_port": "left", "flow": "feedback", "label": "No"},
            {"source": "error", "target": "input", "source_port": "top", "target_port": "right", "flow": "feedback"},
            {"source": "create", "target": "end", "source_port": "bottom", "target_port": "top", "flow": "control"}
        ]
    },
    "sequence-style1": {
        "template_type": "sequence", "style": 1,
        "width": 960, "height": 700,
        "title": "API Request Sequence", "subtitle": "Service interaction timeline",
        "nodes": [
            {"id": "client", "kind": "rect", "x": 60, "y": 120, "width": 130, "height": 50, "label": "Client"},
            {"id": "gateway", "kind": "double_rect", "x": 260, "y": 120, "width": 150, "height": 60, "label": "Gateway"},
            {"id": "auth_svc", "kind": "rect", "x": 490, "y": 120, "width": 130, "height": 50, "label": "Auth Service"},
            {"id": "backend", "kind": "rect", "x": 700, "y": 120, "width": 130, "height": 50, "label": "Backend"},
            {"id": "db", "kind": "cylinder", "x": 720, "y": 350, "width": 130, "height": 90, "label": "Database"}
        ],
        "arrows": [
            {"source": "client", "target": "gateway", "source_port": "right", "target_port": "left", "flow": "control", "label": "request"},
            {"source": "gateway", "target": "auth_svc", "source_port": "right", "target_port": "left", "flow": "control", "label": "verify"},
            {"source": "gateway", "target": "backend", "source_port": "right", "target_port": "left", "flow": "read", "label": "forward"},
            {"source": "backend", "target": "db", "source_port": "bottom", "target_port": "top", "flow": "read"},
            {"source": "auth_svc", "target": "gateway", "source_port": "bottom", "target_port": "bottom", "flow": "feedback", "label": "token", "dashed": True}
        ]
    },
    "comparison-style1": {
        "template_type": "comparison", "style": 1,
        "width": 960, "height": 620,
        "title": "REST vs GraphQL", "subtitle": "API paradigm comparison",
        "containers": [
            {"x": 40, "y": 110, "width": 410, "height": 400, "label": "REST API"},
            {"x": 510, "y": 110, "width": 410, "height": 400, "label": "GraphQL"}
        ],
        "nodes": [
            {"id": "r1", "kind": "rect", "x": 100, "y": 170, "width": 280, "height": 50, "label": "Multiple Endpoints"},
            {"id": "r2", "kind": "rect", "x": 100, "y": 260, "width": 280, "height": 50, "label": "Fixed Data Structure"},
            {"id": "r3", "kind": "rect", "x": 100, "y": 350, "width": 280, "height": 50, "label": "HTTP Caching"},
            {"id": "g1", "kind": "rect", "x": 570, "y": 170, "width": 280, "height": 50, "label": "Single Endpoint"},
            {"id": "g2", "kind": "rect", "x": 570, "y": 260, "width": 280, "height": 50, "label": "Flexible Queries"},
            {"id": "g3", "kind": "rect", "x": 570, "y": 350, "width": 280, "height": 50, "label": "Client-side Caching"}
        ],
        "arrows": [
            {"source": "r1", "target": "g1", "source_port": "right", "target_port": "left", "flow": "neutral", "dashed": True},
            {"source": "r2", "target": "g2", "source_port": "right", "target_port": "left", "flow": "neutral", "dashed": True},
            {"source": "r3", "target": "g3", "source_port": "right", "target_port": "left", "flow": "neutral", "dashed": True}
        ]
    },
    "timeline-style1": {
        "template_type": "timeline", "style": 1,
        "width": 960, "height": 520,
        "title": "Project Milestones", "subtitle": "2026 Q1-Q2 delivery timeline",
        "nodes": [
            {"id": "m1", "kind": "rect", "x": 60, "y": 180, "width": 150, "height": 55, "label": "Kickoff", "sublabel": "Jan 15"},
            {"id": "m2", "kind": "rect", "x": 270, "y": 180, "width": 150, "height": 55, "label": "Alpha", "sublabel": "Feb 28"},
            {"id": "m3", "kind": "rect", "x": 480, "y": 180, "width": 150, "height": 55, "label": "Beta", "sublabel": "Apr 1"},
            {"id": "m4", "kind": "rect", "x": 690, "y": 180, "width": 150, "height": 55, "label": "Launch", "sublabel": "May 30"},
            {"id": "team", "kind": "rect", "x": 60, "y": 340, "width": 120, "height": 50, "label": "Team A"},
            {"id": "infra", "kind": "rect", "x": 270, "y": 340, "width": 120, "height": 50, "label": "DevOps"},
            {"id": "qa", "kind": "rect", "x": 480, "y": 340, "width": 120, "height": 50, "label": "QA Team"}
        ],
        "arrows": [
            {"source": "m1", "target": "m2", "source_port": "right", "target_port": "left", "flow": "control"},
            {"source": "m2", "target": "m3", "source_port": "right", "target_port": "left", "flow": "control"},
            {"source": "m3", "target": "m4", "source_port": "right", "target_port": "left", "flow": "control"},
            {"source": "team", "target": "m1", "source_port": "top", "target_port": "bottom", "flow": "read"},
            {"source": "infra", "target": "m2", "source_port": "top", "target_port": "bottom", "flow": "read"},
            {"source": "qa", "target": "m3", "source_port": "top", "target_port": "bottom", "flow": "read"}
        ]
    },
    "mind-map-style1": {
        "template_type": "mind-map", "style": 1,
        "width": 960, "height": 620,
        "title": "System Design", "subtitle": "Core components mind map",
        "nodes": [
            {"id": "core", "kind": "hexagon", "x": 380, "y": 250, "width": 180, "height": 80, "label": "System"},
            {"id": "fe", "kind": "rect", "x": 80, "y": 100, "width": 140, "height": 50, "label": "Frontend"},
            {"id": "be", "kind": "rect", "x": 80, "y": 400, "width": 140, "height": 50, "label": "Backend"},
            {"id": "db", "kind": "cylinder", "x": 80, "y": 500, "width": 130, "height": 80, "label": "Database"},
            {"id": "auth", "kind": "rect", "x": 380, "y": 80, "width": 140, "height": 50, "label": "Auth"},
            {"id": "cache", "kind": "rect", "x": 700, "y": 100, "width": 140, "height": 50, "label": "Cache"},
            {"id": "mq", "kind": "rect", "x": 700, "y": 400, "width": 140, "height": 50, "label": "Queue"},
            {"id": "monitor", "kind": "rect", "x": 700, "y": 500, "width": 140, "height": 50, "label": "Monitoring"}
        ],
        "arrows": [
            {"source": "core", "target": "fe", "source_port": "left", "target_port": "right", "flow": "control"},
            {"source": "core", "target": "be", "source_port": "left", "target_port": "right", "flow": "control"},
            {"source": "be", "target": "db", "source_port": "bottom", "target_port": "top", "flow": "data"},
            {"source": "core", "target": "auth", "source_port": "top", "target_port": "bottom", "flow": "control"},
            {"source": "core", "target": "cache", "source_port": "right", "target_port": "left", "flow": "read"},
            {"source": "core", "target": "mq", "source_port": "right", "target_port": "left", "flow": "write"},
            {"source": "mq", "target": "monitor", "source_port": "bottom", "target_port": "top", "flow": "data"}
        ]
    },
    "agent-style1": {
        "template_type": "agent", "style": 1,
        "width": 960, "height": 700,
        "title": "AI Agent Architecture", "subtitle": "Tool-use agent with memory",
        "containers": [
            {"x": 36, "y": 96, "width": 888, "height": 220, "label": "AGENT CORE"},
            {"x": 36, "y": 350, "width": 888, "height": 130, "label": "TOOLS"},
            {"x": 36, "y": 510, "width": 888, "height": 120, "label": "MEMORY"}
        ],
        "nodes": [
            {"id": "llm", "kind": "hexagon", "x": 350, "y": 140, "width": 180, "height": 80, "label": "LLM"},
            {"id": "planner", "kind": "rect", "x": 120, "y": 200, "width": 150, "height": 50, "label": "Planner"},
            {"id": "executor", "kind": "rect", "x": 620, "y": 200, "width": 150, "height": 50, "label": "Executor"},
            {"id": "search", "kind": "rect", "x": 80, "y": 380, "width": 150, "height": 50, "label": "Web Search"},
            {"id": "code", "kind": "rect", "x": 300, "y": 380, "width": 150, "height": 50, "label": "Code Exec"},
            {"id": "api_tool", "kind": "rect", "x": 520, "y": 380, "width": 150, "height": 50, "label": "API Call"},
            {"id": "file", "kind": "rect", "x": 740, "y": 380, "width": 130, "height": 50, "label": "File I/O"},
            {"id": "stm", "kind": "rect", "x": 120, "y": 550, "width": 150, "height": 50, "label": "Working Mem"},
            {"id": "ltm", "kind": "cylinder", "x": 400, "y": 540, "width": 150, "height": 80, "label": "Long-term"},
            {"id": "ctx", "kind": "rect", "x": 660, "y": 550, "width": 150, "height": 50, "label": "Context"}
        ],
        "arrows": [
            {"source": "planner", "target": "llm", "source_port": "right", "target_port": "left", "flow": "control"},
            {"source": "llm", "target": "executor", "source_port": "right", "target_port": "left", "flow": "control"},
            {"source": "executor", "target": "search", "source_port": "bottom", "target_port": "top", "flow": "control"},
            {"source": "executor", "target": "code", "source_port": "bottom", "target_port": "top", "flow": "control"},
            {"source": "executor", "target": "api_tool", "source_port": "bottom", "target_port": "top", "flow": "control"},
            {"source": "llm", "target": "stm", "source_port": "bottom", "target_port": "top", "flow": "read"},
            {"source": "llm", "target": "ltm", "source_port": "bottom", "target_port": "top", "flow": "data"},
            {"source": "executor", "target": "ctx", "source_port": "bottom", "target_port": "top", "flow": "write"}
        ]
    },
    "use-case-style1": {
        "template_type": "use-case", "style": 1,
        "width": 960, "height": 600,
        "title": "E-Commerce Use Cases", "subtitle": "Actor and use case diagram",
        "nodes": [
            {"id": "user", "kind": "person", "x": 80, "y": 200, "width": 100, "height": 120, "label": "Customer"},
            {"id": "admin", "kind": "person", "x": 80, "y": 420, "width": 100, "height": 120, "label": "Admin"},
            {"id": "browse", "kind": "ellipse_node", "x": 350, "y": 120, "width": 160, "height": 60, "label": "Browse Products"},
            {"id": "cart", "kind": "ellipse_node", "x": 350, "y": 240, "width": 160, "height": 60, "label": "Add to Cart"},
            {"id": "checkout", "kind": "ellipse_node", "x": 350, "y": 360, "width": 160, "height": 60, "label": "Checkout"},
            {"id": "manage", "kind": "ellipse_node", "x": 350, "y": 460, "width": 160, "height": 60, "label": "Manage Products"},
            {"id": "pay", "kind": "rect", "x": 650, "y": 300, "width": 150, "height": 55, "label": "Payment"},
            {"id": "inventory", "kind": "rect", "x": 650, "y": 440, "width": 150, "height": 55, "label": "Inventory"}
        ],
        "arrows": [
            {"source": "user", "target": "browse", "source_port": "right", "target_port": "left", "flow": "control"},
            {"source": "user", "target": "cart", "source_port": "right", "target_port": "left", "flow": "control"},
            {"source": "user", "target": "checkout", "source_port": "right", "target_port": "left", "flow": "control"},
            {"source": "checkout", "target": "pay", "source_port": "right", "target_port": "left", "flow": "data"},
            {"source": "admin", "target": "manage", "source_port": "right", "target_port": "left", "flow": "write"},
            {"source": "manage", "target": "inventory", "source_port": "right", "target_port": "left", "flow": "write"}
        ]
    },
    "class-style1": {
        "template_type": "class", "style": 1,
        "width": 960, "height": 700,
        "title": "Domain Model", "subtitle": "Class hierarchy diagram",
        "nodes": [
            {"id": "base", "kind": "rect", "x": 360, "y": 80, "width": 200, "height": 80, "label": "BaseEntity", "sublabel": "id, createdAt"},
            {"id": "user_cls", "kind": "rect", "x": 120, "y": 250, "width": 200, "height": 80, "label": "User", "sublabel": "name, email"},
            {"id": "order", "kind": "rect", "x": 360, "y": 250, "width": 200, "height": 80, "label": "Order", "sublabel": "total, status"},
            {"id": "product", "kind": "rect", "x": 600, "y": 250, "width": 200, "height": 80, "label": "Product", "sublabel": "name, price"},
            {"id": "addr", "kind": "rect", "x": 120, "y": 430, "width": 200, "height": 80, "label": "Address", "sublabel": "street, city"},
            {"id": "item", "kind": "rect", "x": 600, "y": 430, "width": 200, "height": 80, "label": "OrderItem", "sublabel": "qty, price"},
            {"id": "cat", "kind": "rect", "x": 600, "y": 580, "width": 200, "height": 60, "label": "Category", "sublabel": "name"}
        ],
        "arrows": [
            {"source": "user_cls", "target": "base", "source_port": "top", "target_port": "bottom", "flow": "control"},
            {"source": "order", "target": "base", "source_port": "top", "target_port": "bottom", "flow": "control"},
            {"source": "product", "target": "base", "source_port": "top", "target_port": "bottom", "flow": "control"},
            {"source": "user_cls", "target": "addr", "source_port": "bottom", "target_port": "top", "flow": "data"},
            {"source": "order", "target": "item", "source_port": "right", "target_port": "left", "flow": "data"},
            {"source": "product", "target": "cat", "source_port": "bottom", "target_port": "top", "flow": "data"},
            {"source": "item", "target": "product", "source_port": "top", "target_port": "bottom", "flow": "read", "dashed": True}
        ]
    },
    "state-machine-style1": {
        "template_type": "state-machine", "style": 1,
        "width": 960, "height": 620,
        "title": "Order State Machine", "subtitle": "E-commerce order lifecycle",
        "nodes": [
            {"id": "created", "kind": "stadium", "x": 60, "y": 200, "width": 150, "height": 50, "label": "Created"},
            {"id": "paid", "kind": "rect", "x": 280, "y": 200, "width": 150, "height": 55, "label": "Paid"},
            {"id": "shipped", "kind": "rect", "x": 500, "y": 200, "width": 150, "height": 55, "label": "Shipped"},
            {"id": "delivered", "kind": "rect", "x": 720, "y": 200, "width": 150, "height": 55, "label": "Delivered"},
            {"id": "cancelled", "kind": "rect", "x": 280, "y": 380, "width": 150, "height": 55, "label": "Cancelled"},
            {"id": "returned", "kind": "rect", "x": 620, "y": 380, "width": 150, "height": 55, "label": "Returned"}
        ],
        "arrows": [
            {"source": "created", "target": "paid", "source_port": "right", "target_port": "left", "flow": "control", "label": "pay"},
            {"source": "paid", "target": "shipped", "source_port": "right", "target_port": "left", "flow": "control", "label": "ship"},
            {"source": "shipped", "target": "delivered", "source_port": "right", "target_port": "left", "flow": "control", "label": "deliver"},
            {"source": "created", "target": "cancelled", "source_port": "bottom", "target_port": "top", "flow": "feedback", "label": "cancel"},
            {"source": "paid", "target": "cancelled", "source_port": "bottom", "target_port": "right", "flow": "feedback"},
            {"source": "delivered", "target": "returned", "source_port": "bottom", "target_port": "right", "flow": "feedback", "label": "return"}
        ]
    },
    "er-diagram-style1": {
        "template_type": "er-diagram", "style": 1,
        "width": 960, "height": 680,
        "title": "E-Commerce ER Diagram", "subtitle": "Entity relationship model",
        "nodes": [
            {"id": "users", "kind": "rect", "x": 100, "y": 150, "width": 180, "height": 100, "label": "Users", "sublabel": "id, name, email"},
            {"id": "orders", "kind": "rect", "x": 400, "y": 150, "width": 180, "height": 100, "label": "Orders", "sublabel": "id, total, status"},
            {"id": "products", "kind": "rect", "x": 700, "y": 150, "width": 180, "height": 100, "label": "Products", "sublabel": "id, name, price"},
            {"id": "items", "kind": "rect", "x": 400, "y": 380, "width": 180, "height": 100, "label": "Order Items", "sublabel": "qty, unit_price"},
            {"id": "reviews", "kind": "rect", "x": 100, "y": 380, "width": 180, "height": 100, "label": "Reviews", "sublabel": "rating, comment"},
            {"id": "cats", "kind": "rect", "x": 700, "y": 380, "width": 180, "height": 80, "label": "Categories", "sublabel": "name, slug"}
        ],
        "arrows": [
            {"source": "users", "target": "orders", "source_port": "right", "target_port": "left", "flow": "control", "label": "1:N"},
            {"source": "orders", "target": "items", "source_port": "bottom", "target_port": "top", "flow": "data", "label": "1:N"},
            {"source": "products", "target": "items", "source_port": "bottom", "target_port": "right", "flow": "read", "label": "1:N"},
            {"source": "users", "target": "reviews", "source_port": "bottom", "target_port": "top", "flow": "write", "label": "1:N"},
            {"source": "products", "target": "reviews", "source_port": "bottom", "target_port": "right", "flow": "read", "label": "1:N"},
            {"source": "cats", "target": "products", "source_port": "top", "target_port": "bottom", "flow": "control", "label": "1:N"}
        ]
    },
    "network-topology-style1": {
        "template_type": "network-topology", "style": 1,
        "width": 960, "height": 620,
        "title": "Network Topology", "subtitle": "Datacenter network layout",
        "containers": [
            {"x": 36, "y": 96, "width": 888, "height": 160, "label": "PUBLIC ZONE"},
            {"x": 36, "y": 290, "width": 888, "height": 160, "label": "PRIVATE ZONE"},
            {"x": 36, "y": 484, "width": 888, "height": 110, "label": "DATA ZONE"}
        ],
        "nodes": [
            {"id": "cdn", "kind": "rect", "x": 100, "y": 140, "width": 140, "height": 50, "label": "CDN"},
            {"id": "lb", "kind": "hexagon", "x": 350, "y": 130, "width": 160, "height": 70, "label": "Load Balancer"},
            {"id": "fw", "kind": "rect", "x": 620, "y": 140, "width": 140, "height": 50, "label": "Firewall"},
            {"id": "web1", "kind": "rect", "x": 100, "y": 330, "width": 140, "height": 50, "label": "Web Server 1"},
            {"id": "web2", "kind": "rect", "x": 350, "y": 330, "width": 140, "height": 50, "label": "Web Server 2"},
            {"id": "app", "kind": "double_rect", "x": 600, "y": 325, "width": 160, "height": 60, "label": "App Server"},
            {"id": "db1", "kind": "cylinder", "x": 150, "y": 510, "width": 130, "height": 80, "label": "DB Primary"},
            {"id": "db2", "kind": "cylinder", "x": 420, "y": 510, "width": 130, "height": 80, "label": "DB Replica"},
            {"id": "cache", "kind": "rect", "x": 700, "y": 520, "width": 130, "height": 50, "label": "Redis"}
        ],
        "arrows": [
            {"source": "cdn", "target": "lb", "source_port": "right", "target_port": "left", "flow": "read"},
            {"source": "lb", "target": "fw", "source_port": "right", "target_port": "left", "flow": "control"},
            {"source": "fw", "target": "web1", "source_port": "bottom", "target_port": "top", "flow": "control"},
            {"source": "fw", "target": "web2", "source_port": "bottom", "target_port": "top", "flow": "control"},
            {"source": "fw", "target": "app", "source_port": "bottom", "target_port": "top", "flow": "control"},
            {"source": "web1", "target": "db1", "source_port": "bottom", "target_port": "top", "flow": "data"},
            {"source": "web2", "target": "db2", "source_port": "bottom", "target_port": "top", "flow": "read"},
            {"source": "app", "target": "cache", "source_port": "bottom", "target_port": "top", "flow": "read"},
            {"source": "db1", "target": "db2", "source_port": "right", "target_port": "left", "flow": "async", "dashed": True}
        ]
    }
}

errors = []
for name, data in fixtures.items():
    json_path = os.path.join(FIXTURE_DIR, f"{name}.json")
    svg_path = os.path.join(OUTPUT_DIR, f"{name}.svg")
    html_path = os.path.join(OUTPUT_DIR, f"{name}-preview.html")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"--- {name} ({data['template_type']}) ---", flush=True)

    r = subprocess.run(
        ["python3", SCRIPT, data["template_type"], svg_path],
        input=json.dumps(data), capture_output=True, text=True, encoding="utf-8"
    )
    if r.returncode != 0:
        print(f"  ERROR: {r.stderr.strip()}")
        errors.append(f"{name}: {r.stderr.strip()}")
        continue
    print(f"  {r.stdout.strip()}")

    r2 = subprocess.run(
        ["python3", PREVIEW_SCRIPT, svg_path, html_path],
        capture_output=True, text=True, encoding="utf-8"
    )
    print(f"  {r2.stdout.strip()}")

print(f"\n=== Done: {len(fixtures)} types, {len(errors)} errors ===")
for e in errors:
    print(f"  FAIL: {e}")
