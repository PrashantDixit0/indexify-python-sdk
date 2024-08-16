from typing import (
    Any,
    List,
    Optional,
    Literal,
    Dict,
    BinaryIO,
    Type,
    cast,
    Mapping,
)
from pydantic import BaseModel, Json, Field
import json
from typing_extensions import Annotated, Doc


class BaseData(BaseModel):
    meta: Mapping[str, Type[BaseModel]]

    def get_features(self) -> List[Type[BaseModel]]:
        return []

    def get_feature(self, name: str) -> Optional[Type[BaseModel]]:
        return self.meta.get(name)


# Copied from FastAPI - https://github.com/fastapi/fastapi/blob/75705617a66300847436e39ba703af1b8d109963/fastapi/datastructures.py#L30
class UploadFile(BaseModel):
    """
    A file uploaded in a request.
    """

    file: Annotated[
        BinaryIO,
        Doc("The standard Python file object (non-async)."),
    ]
    filename: Annotated[Optional[str], Doc("The original file name.")]
    size: Annotated[Optional[int], Doc("The size of the file in bytes.")]
    content_type: Annotated[
        Optional[str], Doc("The content type of the request, from the headers.")
    ]

class Feature(BaseModel):
    feature_type: Literal["embedding", "metadata"]
    name: str
    value: Json
    comment: Optional[Json] = Field(default=None)

    @classmethod
    def embedding(cls, values: List[float], name: str = "embedding", distance="cosine"):
        return cls(
            feature_type="embedding",
            name=name,
            value=json.dumps({"values": values, "distance": distance}),
            comment=None,
        )

    @classmethod
    def metadata(cls, value: Json, comment: Json = None, name: str = "metadata"):
        value = json.dumps(value)
        comment = json.dumps(comment) if comment is not None else None
        return cls(feature_type="metadata", name=name, value=value)


class Content(BaseModel):
    id: Optional[str] = (None,)
    content_type: Optional[str]
    data: bytes
    features: List[Feature] = []

    @classmethod
    def from_text(
        cls,
        text: str,
        features: List[Feature] = [],
    ):
        return Content(
            id=None,
            content_type="text/plain",
            data=bytes(text, "utf-8"),
            features=features,
        )

    @classmethod
    def from_json(cls, json_data: Json, features: List[Feature] = []):
        return cls(
            content_type="application/json",
            data=bytes(json.dumps(json_data), "utf-8"),
            features=features,
        )

    @classmethod
    def from_file(cls, path: str):
        import mimetypes

        m, _ = mimetypes.guess_type(path)
        with open(path, "rb") as f:
            return cls(id="none-for-now", content_type=m, data=f.read())


class ContentMetadata(BaseModel):
    id: str
    parent_id: str
    labels: Dict[str, Any]
    extraction_graph_names: List[str]
    extraction_policy: str
    mime_type: str
    extracted_metadata: Dict[str, Any] = {}

    @classmethod
    def from_dict(cls, json: Dict):
        return cls(
            id=json["id"],
            parent_id=json["parent_id"],
            labels=json["labels"],
            extraction_graph_names=json["extraction_graph_names"],
            extraction_policy=json["source"],
            mime_type=json["mime_type"],
            extracted_metadata=json["extracted_metadata"],
        )
