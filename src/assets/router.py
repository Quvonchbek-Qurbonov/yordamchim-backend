from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Response
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.assets.imagekit import client as imagekit
from src.services.models import Service
from src.assets.models import ServiceImage


router = APIRouter(prefix="/assets", tags=["Service Images"])


@router.post("/services/images/{service_id}", status_code=status.HTTP_201_CREATED)
async def upload_service_image(
    service_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    response = imagekit.files.upload(
        file=file.file,
        file_name=file.filename or f"service_{service_id}.jpg",
        use_unique_file_name=True,
        folder="/serviceImages"
    )

    if not response:
        raise HTTPException(status_code=502, detail="ImageKit upload failed")

    image = ServiceImage(
        service_id=service_id,
        imagekit_file_id=response.file_id,
        url=response.url,
        thumbnail_url=response.thumbnail_url,
        file_path=response.file_path,
        file_name=response.name,
        file_type=response.file_type,
        size=response.size,
        is_primary=False
    )
    db.add(image)
    db.commit()
    db.refresh(image)

    return {
        "id": image.id,
        "service_id": image.service_id,
        "imagekit_file_id": image.imagekit_file_id,
        "url": image.url,
        "thumbnail_url": image.thumbnail_url,
        "file_path": image.file_path,
        "file_name": image.file_name,
        "file_type": image.file_type,
        "size": image.size,
        "is_primary": image.is_primary
    }

@router.get("/services/images/{service_id}", status_code=status.HTTP_200_OK)
def list_service_images(service_id: int, db: Session = Depends(get_db)):
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    images = (
        db.query(ServiceImage)
        .filter(ServiceImage.service_id == service_id)
        .order_by(ServiceImage.is_primary.desc(), ServiceImage.id.desc())
        .all()
    )

    return [
        {
            "id": img.id,
            "service_id": img.service_id,
            "imagekit_file_id": img.imagekit_file_id,
            "url": img.url,
            "thumbnail_url": img.thumbnail_url,
            "file_path": img.file_path,
            "file_name": img.file_name,
            "file_type": img.file_type,
            "size": img.size,
            "is_primary": img.is_primary,
        }
        for img in images
    ]


@router.delete("/services/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service_image(image_id: int, db: Session = Depends(get_db)):
    image = db.query(ServiceImage).filter(ServiceImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    try:
        imagekit.files.delete(file_id=image.imagekit_file_id)
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Failed to delete image from ImageKit",
        )

    db.delete(image)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/services/images/{image_id}/primary", status_code=status.HTTP_200_OK)
def set_primary_service_image(image_id: int, db: Session = Depends(get_db)):
    image = db.query(ServiceImage).filter(ServiceImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # unset previous primary for same service
    (
        db.query(ServiceImage)
        .filter(
            ServiceImage.service_id == image.service_id,
            ServiceImage.is_primary.is_(True),
            ServiceImage.id != image.id,
        )
        .update({"is_primary": False}, synchronize_session=False)
    )

    image.is_primary = True
    db.add(image)
    db.commit()
    db.refresh(image)

    return {
        "id": image.id,
            "service_id": image.service_id,
            "imagekit_file_id": image.imagekit_file_id,
            "url": image.url,
            "thumbnail_url": image.thumbnail_url,
            "file_path": image.file_path,
            "file_name": image.file_name,
            "file_type": image.file_type,
            "size": image.size,
            "is_primary": image.is_primary,
    }