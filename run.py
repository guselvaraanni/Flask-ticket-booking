import os

import uvicorn
from dotenv import load_dotenv

load_dotenv()

if __name__ == '__main__':
    uvicorn.run(
        'app.main:app',
        host=os.getenv('HOST', 'localhost'),
        port=int(os.getenv('PORT', '8000')),
        reload=os.getenv('DEBUG', 'true').lower() in ('1', 'true', 'yes'),
    )
