from pydantic import BaseModel


class OntologyTermResponse(BaseModel):
    term_id: str
    label: str
    synonyms: list[str] = []
    ontology: str
