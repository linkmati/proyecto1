from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from supabase import Client
from app.db.supabase import get_supabase, get_supabase_admin
from app.models.schemas import UserCreate, TokenResponse

# We use "Auth" as the tag to group these routes in the automatic documentation (Swagger)
router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/register")
def register_user(
    user_data: UserCreate, 
    db: Client = Depends(get_supabase),
    admin_db: Client = Depends(get_supabase_admin)
):
    """
    Handles new user registration. 
    It creates the user in Supabase Auth and then syncs the profile to our public table.
    """
    try:
        # Step 1: Attempt to register the user in Supabase Authentication
        # This part handles the email and password securely
        auth_response = db.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password
        })
        
        # If Supabase doesn't return a user object, something went wrong
        if not auth_response.user:
            raise HTTPException(
                status_code=400, 
                detail="Registration failed. Check if email is valid or already exists."
            )

        new_user_id = auth_response.user.id

        # Step 2: Sync user data with our custom 'usuarios' table
        # We use 'admin_db' here because it bypasses safety rules (RLS), 
        # allowing us to create the profile even before the user logs in fully.
        admin_db.table("usuarios").upsert({
            "id_usuario": new_user_id,
            "email": user_data.email,
            "estado": "activo"
        }).execute()
        
        return {
            "message": "User registered successfully!", 
            "id_usuario": new_user_id
        }
        
    except Exception as error:
        # We log the error in the console and send a friendly message to the student/client
        print(f"DEBUG - Registration Error: {str(error)}")
        
        # If it's already an HTTPException, we just re-raise it
        if isinstance(error, HTTPException):
            raise error
            
        # For any other unexpected error, we send a 400 Bad Request
        raise HTTPException(status_code=400, detail=str(error))

@router.post("/login", response_model=TokenResponse)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Client = Depends(get_supabase),
    admin_db: Client = Depends(get_supabase_admin)
):
    """
    Authenticates a user and returns a token.
    FastAPI's OAuth2PasswordRequestForm expects 'username' (which is the email) and 'password'.
    """
    try:
        # Step 1: Sign in with email and password
        auth_response = db.auth.sign_in_with_password({
            "email": form_data.username, 
            "password": form_data.password
        })
        
        if not auth_response.user:
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        # Step 2: Ensure the user profile exists in our custom table (Sync Check)
        # This is helpful in case the user was created but the sync failed earlier.
        admin_db.table("usuarios").upsert({
            "id_usuario": auth_response.user.id,
            "email": auth_response.user.email,
            "estado": "activo"
        }).execute()
        
        # Step 3: Return the access token needed for future requests
        return {
            "access_token": auth_response.session.access_token, 
            "token_type": "bearer"
        }
        
    except Exception as error:
        print(f"DEBUG - Login Error: {str(error)}")
        raise HTTPException(status_code=401, detail="Could not authenticate user. Check credentials.")
