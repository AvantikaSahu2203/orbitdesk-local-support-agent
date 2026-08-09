import json
import os
import sys
import http.server
from pathlib import Path

# Add current workspace directory to Python system path to search components
sys.path.append(str(Path(__file__).resolve().parent))

from graph import graph

PORT = 8000

class LocalSupportHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress default server console log spam for cleaner console output
        pass

    def do_GET(self):
        # Serve UI Client
        if self.path in ("/", "/index.html"):
            index_path = Path(__file__).resolve().parent / "index.html"
            if not index_path.exists():
                self.send_error(404, "index.html file not found")
                return

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            
            with open(index_path, "r", encoding="utf-8") as f:
                self.wfile.write(f.read().encode("utf-8"))
        else:
            self.send_error(404, "File Not Found")

    def do_POST(self):
        # API Chat Endpoint to trigger support LangGraph agent
        if self.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            
            try:
                data = json.loads(post_data)
                question = data.get("question", "").strip()
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Invalid JSON body: {str(e)}"}).encode("utf-8"))
                return

            if not question:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Question parameter is required"}).encode("utf-8"))
                return

            print(f"\n[HTTP Server] Processing query: \"{question}\"")
            
            # Formulate graph initial execution state
            initial_state = {
                "question": question,
                "classification": "answerable",
                "answer": "",
                "retrieved_documents": [],
                "verification_passed": False,
                "verification_reason": "",
                "revision_count": 0,
                "logs": [],
                "generation_latency": 0.0,
                "model_load_time": 0.0,
            }

            try:
                # Execute compiled LangGraph workflow
                result = graph.invoke(initial_state)
                
                # Filter/extract state response data safely
                response_data = {
                    "question": result.get("question", ""),
                    "classification": result.get("classification", "answerable"),
                    "answer": result.get("answer", ""),
                    "retrieved_documents": result.get("retrieved_documents", []),
                    "verification_passed": result.get("verification_passed", False),
                    "verification_reason": result.get("verification_reason", ""),
                    "revision_count": result.get("revision_count", 0),
                    "generation_latency": result.get("generation_latency", 0.0),
                    "model_load_time": result.get("model_load_time", 0.0),
                    "logs": result.get("logs", []),
                }

                self.send_response(200)
                self.send_header("Content-type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode("utf-8"))
                print(f"[HTTP Server] Query finished. Routes to: {response_data['classification']}, verification_passed={response_data['verification_passed']}\n")

            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Internal agent execution error: {str(e)}"}).encode("utf-8"))
        else:
            self.send_error(404, "Endpoint Not Found")

def run():
    server_address = ("", PORT)
    httpd = http.server.HTTPServer(server_address, LocalSupportHandler)
    print(f"\n" + "="*80)
    print(f" OrbitDesk Support Agent Web Server started on http://localhost:{PORT}")
    print(f" Open http://localhost:{PORT} in your web browser to test the UI.")
    print(f" Press Ctrl+C to stop the server.")
    print("="*80 + "\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping OrbitDesk Support Agent Web Server...")
        httpd.server_close()

if __name__ == "__main__":
    run()
