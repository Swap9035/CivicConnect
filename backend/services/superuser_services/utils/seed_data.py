from services.superuser_services.models.staff_user import StaffUser, UserRole, Department, StaffMetadata, AccountStatus
from services.superuser_services.db.repositories.user_repository import user_repository
from services.superuser_services.utils.auth import auth_utils
from services.superuser_services.config import settings
import logging
import uuid

logger = logging.getLogger(__name__)

async def create_initial_superadmin():
    """Create initial SuperAdmin user if not exists"""
    try:
        # Check if SuperAdmin already exists
        existing_admin = await user_repository.get_user_by_email(settings.initial_admin_email)
        if existing_admin:
            logger.info("SuperAdmin already exists")
            return
        
        # Create SuperAdmin
        staff_id = f"SUPER_{uuid.uuid4().hex[:6].upper()}"
        hashed_password = auth_utils.hash_password(settings.initial_admin_password)
        
        superadmin = StaffUser(
            staff_id=staff_id,
            full_name="System SuperAdmin",
            employee_id="SUPER_ADMIN_001",
            email=settings.initial_admin_email,
            phone_number="+911234567890",
            password_hash=hashed_password,
            role=UserRole.SUPER_ADMIN,
            metadata=StaffMetadata(
                dept=Department.ELECTRICITY,  # Default department
                ward="System",
                designation="System Administrator"
            ),
            account_status=AccountStatus(
                is_active=True,
                is_first_login=False,  # SuperAdmin doesn't need first login flow
                created_by="SYSTEM"
            )
        )
        
        await user_repository.create_user(superadmin)
        logger.info(f"SuperAdmin created successfully with ID: {staff_id}")
        logger.info(f"SuperAdmin credentials - Email: {settings.initial_admin_email}, Password: {settings.initial_admin_password}")
        
    except Exception as e:
        logger.error(f"Error creating SuperAdmin: {e}")
        raise

async def seed_sample_data():
    """Create sample department admins and officers"""
    try:
        # Sample Department Admin
        dept_admin_id = f"DEPT_{uuid.uuid4().hex[:6].upper()}"
        dept_admin = StaffUser(
            staff_id=dept_admin_id,
            full_name="Electricity Dept Admin",
            employee_id="ELEC_ADMIN_001",
            email="elec.admin@gov.in",
            phone_number="+911234567891",
            password_hash=auth_utils.hash_password("ElecAdmin@123"),
            role=UserRole.DEPT_ADMIN,
            metadata=StaffMetadata(
                dept=Department.ELECTRICITY,
                ward="Central Zone",
                designation="Electrical Superintendent"
            ),
            account_status=AccountStatus(
                is_active=True,
                is_first_login=False,
                created_by="SYSTEM"
            )
        )
        
        # Sample Nodal Officer
        officer_id = f"STF_{uuid.uuid4().hex[:6].upper()}"
        nodal_officer = StaffUser(
            staff_id=officer_id,
            full_name="Rahul Sharma",
            employee_id="ELEC_OFF_001",
            email="rahul.sharma@gov.in",
            phone_number="+911234567892",
            password_hash=auth_utils.hash_password("Officer@123"),
            role=UserRole.NODAL_OFFICER,
            metadata=StaffMetadata(
                dept=Department.ELECTRICITY,
                ward="Shanti Nagar",
                designation="Junior Engineer"
            ),
            account_status=AccountStatus(
                is_active=True,
                is_first_login=True,
                created_by=dept_admin_id
            )
        )
        
        # Check and create if not exists
        if not await user_repository.get_user_by_email("elec.admin@gov.in"):
            await user_repository.create_user(dept_admin)
            logger.info("Sample Department Admin created")
        
        if not await user_repository.get_user_by_email("rahul.sharma@gov.in"):
            await user_repository.create_user(nodal_officer)
            logger.info("Sample Nodal Officer created")
            
    except Exception as e:
        logger.error(f"Error creating sample data: {e}")
