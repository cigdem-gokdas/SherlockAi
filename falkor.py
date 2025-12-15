"""
Module for handling FalkorDB (Graph Database) operations.

This module manages connections to FalkorDB and saves movie/series data
with relationship structures. Includes error handling for offline scenarios.
"""
from dotenv import load_dotenv
from falkordb import FalkorDB

load_dotenv()


class FalkorManager:
    """
    Manages connection to FalkorDB graph database.

    Handles node creation, relationship linking, and graceful degradation
    when FalkorDB or Docker is unavailable.
    """

    # pylint: disable=too-few-public-methods
    def __init__(self):
        """Initialize connection settings and database connection."""
        self.host = "localhost"
        self.port = 6379
        self.client = None
        self.graph = None
        self.is_active = False

        self._connect()

    def _connect(self):
        """
        Attempt connection to FalkorDB Docker container.

        Sets is_active flag based on connection success.
        """
        try:
            self.client = FalkorDB(host=self.host, port=self.port)
            self.graph = self.client.select_graph("IMDB_Graph")
            self.is_active = True
            print("✔ Connected to FalkorDB (Graph Mode Active)")
        # pylint: disable=broad-exception-caught
        except Exception:
            print("FalkorDB not detected. Running in MongoDB-only mode.")
            self.is_active = False

    def _sanitize_title(self, title: str) -> str:
        """
        Sanitize title for Cypher query safety.
        """
        return title.replace("'", "\\'").replace('"', '\\"')

    def save_media(self, media_item):
        """
        Save media item as node and create relationships in graph.
        """
        if not self.is_active:
            return

        try:
            title = self._sanitize_title(media_item.title)
            year = media_item.year
            rating = media_item.rating
            m_type = "Movie" if media_item.media_type == "movie" else "Series"
            status = media_item.status
            poster_url = media_item.poster_url if media_item.poster_url else ""

            # Create main node
            node_query = f"""
            MERGE (m:{m_type} {{title: '{title}'}})
            SET m.year = '{year}',
                m.rating = '{rating}',
                m.status = '{status}',
                m.poster = '{poster_url}'
            RETURN m
            """

            self.graph.query(node_query)
            print(f" Synced to FalkorDB Graph: {media_item.title}")

            # Create hub node and link
            self._create_hub_relationship(title, m_type, status)

            # Link items by status
            self._create_status_relationships(title, m_type, status)

        # pylint: disable=broad-exception-caught
        except Exception as error:
            print(f"FalkorDB Error: {error}")

    def _create_hub_relationship(self, title: str, m_type: str,
                                 _status: str) -> None:
        """
        Create relationship between media item and category hub.
        """
        try:
            if m_type == "Movie":
                hub_query = f"""
                MERGE (hub:Hub {{name: 'All Movies'}})
                WITH hub
                MATCH (m:Movie {{title: '{title}'}})
                MERGE (m)-[r:BELONGS_TO]->(hub)
                RETURN r
                """
            else:  # Series
                hub_query = f"""
                MERGE (hub:Hub {{name: 'All Series'}})
                WITH hub
                MATCH (s:Series {{title: '{title}'}})
                MERGE (s)-[r:BELONGS_TO]->(hub)
                RETURN r
                """

            self.graph.query(hub_query)

        # pylint: disable=broad-exception-caught
        except Exception:
            pass

    def _create_status_relationships(self, title: str, m_type: str,
                                     status: str) -> None:
        """
        Create relationships between items with same watch status.
        """
        try:
            # Create status hub
            status_hub_query = f"""
            MERGE (hub:StatusHub {{status: '{status}'}})
            RETURN hub
            """
            self.graph.query(status_hub_query)

            # Link media to status hub
            media_to_status = f"""
            MATCH (m:{m_type} {{title: '{title}'}})
            MATCH (hub:StatusHub {{status: '{status}'}})
            MERGE (m)-[r:HAS_STATUS]->(hub)
            RETURN r
            """
            self.graph.query(media_to_status)

            # Link items with same status
            same_status_query = f"""
            MATCH (m1:{m_type} {{status: '{status}'}})
            MATCH (m2:{m_type} {{status: '{status}', title: '{title}'}})
            WHERE m1.title < m2.title
            MERGE (m1)-[r:SAME_STATUS]->(m2)
            RETURN r
            """
            try:
                self.graph.query(same_status_query)
            except Exception:  # pylint: disable=broad-exception-caught
                pass

        # pylint: disable=broad-exception-caught
        except Exception:
            pass


# Global instance for use throughout application
falkor_db = FalkorManager()
