from typing import Union, Optional, List, Type, Tuple, Callable, get_type_hints, Dict
import inspect
from pydantic import BaseModel, Json
from abc import ABC, abstractmethod
from .data import Content, Feature
import json

class EmbeddingSchema(BaseModel):
    dimension: int


class ExtractorMetadata(BaseModel):
    name: str
    description: str
    input_mime_types: List[str]
    # Make this a dynamic model since its a json schema
    input_params: Optional[Dict]

class Extractor(ABC):
    name: str = ""

    version: str = "0.0.0"

    system_dependencies: List[str] = []

    python_dependencies: List[str] = []

    description: str = ""

    input_mime_types = ["text/plain"]

    def extract(
        self, input: Type[BaseModel], params: Type[BaseModel] = None
    ) -> List[Union[Feature, Type[BaseModel]]]:
        """
        Extracts information from the content. Returns a list of features to add
        to the content.
        It can also return a list of Content objects, which will be added to storage
        and any extraction policies defined will be applied to them.
        """
        pass

    def extract_batch(
        self, input_list: List[Type[BaseModel]], params: List[Type[BaseModel]] = None
    ) -> List[List[Union[Feature, Type[BaseModel]]]]:
        """
        Extracts information from the content. Returns a list of features to add
        to the content.
        It can also return a list of Content objects, which will be added to storage
        and any extraction policies defined will be applied to them.
        """
        pass

    @classmethod
    @abstractmethod
    def sample_input(cls) -> Tuple[Content, Type[BaseModel]]:
        pass

    @classmethod
    @abstractmethod
    def embedding_schemas(cls) -> Dict[str, EmbeddingSchema]:
        raise NotImplementedError
    
    def describe(self) -> Dict:
        embedding_schemas = {}
        try:
            embedding_schemas = self.embedding_schemas()
        except NotImplementedError:
            pass

        json_schema = (
            self._param_cls.model_json_schema() if self._param_cls is not None else None
        )

        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "system_dependencies": self.system_dependencies,
            "python_dependencies": self.python_dependencies,
            "input_mime_types": self.input_mime_types,
            "embedding_schemas": embedding_schemas,
            "input_params": json.dumps(json_schema),
        }

def extractor(
    name: Optional[str] = None,
    description: Optional[str] = "",
    version: Optional[str] = "",
    python_dependencies: Optional[List[str]] = None,
    system_dependencies: Optional[List[str]] = None,
    input_mime_types: Optional[List[str]] = None,
    embedding_schemas: Optional[Dict[str, EmbeddingSchema]] = None,
    sample_content: Optional[Callable] = None,
):
    args = locals()
    del args["sample_content"]

    def construct(fn):
        def wrapper():
            hint = get_type_hints(fn).get("params", dict)

            if not args.get("name"):
                args["name"] = (
                    f"{inspect.getmodule(inspect.stack()[1][0]).__name__}:{fn.__name__}"
                )

            class DecoratedFn(Extractor):
                @classmethod
                def extract(cls, input: Type[BaseModel], params: Type[BaseModel]=None) -> List[Content]:  # type: ignore
                    # TODO we can force all the functions to take in a parms object
                    # or check if someone adds a params
                    if params is None:
                        return fn(input)
                    else:
                        return fn(input, params)

                def sample_input(self) -> Content:
                    return sample_content() if sample_content else self.sample_text()

            for key, val in args.items():
                setattr(DecoratedFn, key, val)

            return DecoratedFn

        wrapper._extractor_name = fn.__name__

        return wrapper

    return construct
