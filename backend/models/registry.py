"""Import all ORM models so SQLAlchemy can resolve string relationships."""

import models.ai_chat  # noqa: F401
import models.booking  # noqa: F401
import models.capacity  # noqa: F401
import models.checkin  # noqa: F401
import models.customer_profile  # noqa: F401
import models.dish  # noqa: F401
import models.favorite  # noqa: F401
import models.moderation_log  # noqa: F401
import models.notification  # noqa: F401
import models.owner_profile  # noqa: F401
import models.restaurant  # noqa: F401
import models.restaurant_taxonomy  # noqa: F401
import models.review  # noqa: F401
import models.search_history  # noqa: F401
import models.user  # noqa: F401
