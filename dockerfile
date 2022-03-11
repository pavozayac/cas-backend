FROM python:3.9

# 


WORKDIR /

# 


COPY . .

# 


RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# 



# 

EXPOSE 8000


# CMD ["uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000"]
CMD ["bash", "./run.sh"]