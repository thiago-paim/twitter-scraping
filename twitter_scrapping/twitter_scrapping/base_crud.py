from typing import Generic, List, Optional, Type, TypeVar
from django.db.models import Model
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

ModelType = TypeVar("ModelType", bound=Model)
CreateSchema = TypeVar("CreateSchema", bound=BaseModel)
UpdateSchema = TypeVar("UpdateSchema", bound=BaseModel)


class BaseCRUD(Generic[ModelType, CreateSchema, UpdateSchema]):
	"""
	Base class for all crud operations
	Methods to Create, Read, Update, Delete (CRUD).
	"""
	def __init__(self, model: Type[ModelType]):
		self.model = model

	def get(self, twitter_id: str) -> Optional[ModelType]:
		"""Get a single item."""
		return self.model.objects.get(twitter_id=twitter_id)

	def get_multiple(self, limit:int = 100, offset:int = 0) -> List[ModelType]:
		"""Get multiple items using a query limiting flag."""
		return self.model.objects.all()[offset:offset+limit]

	def create(self, obj_in: CreateSchema) -> ModelType:
		"""Create an item."""
		if not isinstance(obj_in, list):
			obj_in = jsonable_encoder(obj_in)
		return self.model.objects.create(**obj_in)

	def update(self, obj_in: UpdateSchema, twitter_id: str) -> ModelType:
		"""Update an item."""

		if not isinstance(obj_in, list):
			obj_in = jsonable_encoder(obj_in)

		return self.model.objects.filter(twitter_id=twitter_id).update(**obj_in)

	def delete(self, twitter_id: str) -> ModelType:
		"""Delete an item."""
		self.model.objects.filter(twitter_id=twitter_id).delete()
		return {"detail": "Successfully deleted!"}