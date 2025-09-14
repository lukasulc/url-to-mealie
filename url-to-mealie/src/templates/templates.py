from typing import Any, Dict


def get_homepage(url: str, token: str | None) -> str:
    """Generate the homepage HTML."""
    mealie_status = "Connected" if token and url else "Not configured"
    status_class = "success" if token and url else "danger"

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>URL to Mealie - Recipe Parser</title>
    
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Font Awesome Icons -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    
    <!-- Simple Custom Styles -->
    <style>
        body {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .recipe-card {{
            background: white;
            border-radius: 1rem;
            box-shadow: 0 1rem 3rem rgba(0,0,0,.1);
            border-top: 4px solid #667eea;
        }}
        
        .logo-circle {{
            width: 4rem;
            height: 4rem;
            background: linear-gradient(135deg, #667eea, #764ba2);
        }}
        
        .btn-primary {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
        }}
        
        .btn-primary:hover {{
            background: linear-gradient(135deg, #5a6fd8, #6b4190);
            transform: translateY(-1px);
        }}
        
        .platform-badge {{
            font-size: 0.8rem;
        }}
        
        .feature-icon {{
            color: #667eea;
        }}
        
        .input-group-text {{
            background: #f8f9fa;
            border-right: none;
        }}
        
        .form-control {{
            border-left: none;
        }}
        
        .form-control:focus {{
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }}
    </style>
</head>
<body class="d-flex align-items-center py-4">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6 col-lg-5">
                <div class="recipe-card">
                    <!-- Header -->
                    <div class="p-4 text-center border-bottom">
                        <div class="logo-circle rounded-circle d-flex align-items-center justify-content-center mx-auto mb-3">
                            <i class="fas fa-utensils text-white fa-2x"></i>
                        </div>
                        <h1 class="h3 fw-bold text-dark mb-2">URL to Mealie</h1>
                        <p class="text-muted mb-3">Transform social media recipes into organized cooking guides</p>
                        
                        <div class="d-flex justify-content-center mb-2">
                            <span class="badge bg-{status_class} d-flex align-items-center gap-2">
                                <i class="fas {'fa-check-circle' if status_class == 'success' else 'fa-exclamation-triangle'}"></i>
                                Mealie: {mealie_status}
                            </span>
                        </div>
                        
                        {f'<small class="text-muted">{url}</small>' if url else ''}
                    </div>

                    <!-- Form -->
                    <div class="p-4">
                        <form method="post" action="/submit" id="recipeForm">
                            <div class="mb-3">
                                <label for="url" class="form-label fw-semibold">Recipe Video URL</label>
                                <div class="input-group">
                                    <span class="input-group-text">
                                        <i class="fas fa-link text-muted"></i>
                                    </span>
                                    <input 
                                        type="url" 
                                        id="url" 
                                        name="url" 
                                        class="form-control"
                                        placeholder="https://www.instagram.com/p/abc123/"
                                        pattern="^https?:\\/\\/(www\\.)?(instagram\\.com\\/|tiktok\\.com\\/|youtube\\.com\\/).*"
                                        required
                                        autocomplete="url"
                                    >
                                </div>
                                
                                <!-- Supported Platforms -->
                                <div class="d-flex flex-wrap gap-2 mt-2">
                                    <span class="badge bg-light text-dark platform-badge">
                                        <i class="fab fa-instagram text-danger"></i> Instagram
                                    </span>
                                    <span class="badge bg-light text-dark platform-badge">
                                        <i class="fab fa-tiktok text-dark"></i> TikTok
                                    </span>
                                    <span class="badge bg-light text-dark platform-badge">
                                        <i class="fab fa-youtube text-danger"></i> YouTube
                                    </span>
                                    <span class="badge bg-light text-dark platform-badge">
                                        <i class="fas fa-plus"></i> More
                                    </span>
                                </div>
                            </div>

                            <button type="submit" class="btn btn-primary btn-lg w-100 d-flex align-items-center justify-content-center gap-2" id="submitBtn">
                                <i class="fas fa-magic"></i>
                                Parse Recipe
                            </button>
                        </form>
                    </div>
                    <div class="p-4">
                        <a href="/status">
                            <button class="btn btn-secondary btn-lg w-100 d-flex align-items-center justify-content-center gap-2">
                                <i class="fas fa-magic"></i>
                                Check status
                            </button>
                        </a>
                    </div>

                    <!-- Features -->
                    <div class="bg-light p-4 border-top">
                        <h6 class="text-center mb-3 text-muted fw-semibold">What this tool does</h6>
                        <div class="row g-3">
                            <div class="col-6">
                                <div class="d-flex align-items-center gap-2">
                                    <i class="fas fa-download feature-icon"></i>
                                    <small class="text-muted">Downloads video</small>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="d-flex align-items-center gap-2">
                                    <i class="fas fa-microphone feature-icon"></i>
                                    <small class="text-muted">Transcribes audio</small>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="d-flex align-items-center gap-2">
                                    <i class="fas fa-brain feature-icon"></i>
                                    <small class="text-muted">AI parsing</small>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="d-flex align-items-center gap-2">
                                    <i class="fas fa-utensils feature-icon"></i>
                                    <small class="text-muted">Saves to Mealie</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Bootstrap 5 JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        const form = document.getElementById('recipeForm');
        const submitBtn = document.getElementById('submitBtn');
        const urlInput = document.getElementById('url');

        // Form submission handling
        form.addEventListener('submit', function(e) {{
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing Recipe...';
        }});

        // Real-time URL validation
        urlInput.addEventListener('input', function() {{
            const url = this.value;
            const isValid = /^https?:\\/\\/(www\\.)?(instagram\\.com\\/|tiktok\\.com\\/|youtube\\.com\\/).*/.test(url);
            
            if (url && !isValid) {{
                this.classList.add('is-invalid');
            }} else {{
                this.classList.remove('is-invalid');
            }}
        }});

        // Auto-focus
        document.addEventListener('DOMContentLoaded', function() {{
            urlInput.focus();
        }});
    </script>
</body>
</html>
    """


def get_exception_page(error_message: str) -> str:
    """Generate the exception page HTML."""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Validation Error - URL to Mealie</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            body {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
            .error-card {{ background: white; border-radius: 1rem; box-shadow: 0 1rem 3rem rgba(0,0,0,.1); }}
        </style>
    </head>
    <body class="d-flex align-items-center py-4">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="error-card p-5 text-center">
                        <div class="text-danger mb-4">
                            <i class="fas fa-exclamation-triangle fa-4x"></i>
                        </div>
                        <h2 class="h4 mb-3">Invalid URL Format</h2>
                        <p class="text-muted mb-4">Please check your URL and try again:</p>
                        <div class="alert alert-danger text-start">
                            {error_message}
                        </div>
                        <a href="/" class="btn btn-primary">
                            <i class="fas fa-arrow-left me-2"></i>Try Again
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


def get_success_page(recipe_url: str, recipe_name: str, app_state: dict) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Recipe Added Successfully - URL to Mealie</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            body {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
            .success-card {{ background: white; border-radius: 1rem; box-shadow: 0 1rem 3rem rgba(0,0,0,.1); }}
        </style>
    </head>
    <body class="d-flex align-items-center py-4">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-7">
                    <div class="success-card p-5 text-center">
                        <div class="text-success mb-4">
                            <i class="fas fa-check-circle fa-4x"></i>
                        </div>
                        <h2 class="h4 mb-3">Recipe Added Successfully!</h2>
                        <p class="text-muted mb-4">"{recipe_name}" has been parsed and added to your Mealie collection.</p>
                        
                        <div class="d-grid gap-3 d-md-flex justify-content-md-center">
                            <a href="{recipe_url}" class="btn btn-success btn-lg" target="_blank">
                                <i class="fas fa-external-link-alt me-2"></i>View in Mealie
                            </a>
                            <a href="/" class="btn btn-outline-primary btn-lg">
                                <i class="fas fa-plus me-2"></i>Add Another Recipe
                            </a>
                        </div>
                        
                        <div class="alert alert-info mt-4">
                            <i class="fas fa-utensils me-2"></i>
                            <strong>Total Recipes Processed:</strong> {app_state['recipes_processed']}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


def get_error_page(error_message: str, url: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Error Processing Recipe - URL to Mealie</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            body {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
            .error-card {{ background: white; border-radius: 1rem; box-shadow: 0 1rem 3rem rgba(0,0,0,.1); }}
        </style>
    </head>
    <body class="d-flex align-items-center py-4">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="error-card p-5 text-center">
                        <div class="text-danger mb-4">
                            <i class="fas fa-exclamation-circle fa-4x"></i>
                        </div>
                        <h2 class="h4 mb-3">Processing Failed</h2>
                        <p class="text-muted mb-3">We couldn't process your recipe from:</p>
                        <div class="alert alert-secondary">
                            <code class="text-break">{url}</code>
                        </div>
                        <div class="alert alert-danger text-start">
                            <strong>Error:</strong> {error_message}
                        </div>
                        <a href="/" class="btn btn-primary btn-lg">
                            <i class="fas fa-arrow-left me-2"></i>Try Again
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


def get_instagram_error(errors: str, suggestions: str | None = None) -> str:
    return f"""
    <!DOCTYPE html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Instagram Error - URL to Mealie</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            body {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
            .success-card {{ background: white; border-radius: 1rem; box-shadow: 0 1rem 3rem rgba(0,0,0,.1); }}
        </style>
    </head>
    <html lang="en">
        <div class="container my-4">
            <div class="row justify-content-center">
                <div class="col-md-7">
                    <div class="card shadow-sm">
                        <div class="card-body">
                        <div class="text-center mb-3">
                            <i class="fab fa-instagram text-danger fs-1"></i>
                        </div>
                        <h5 class="card-title text-center">Instagram error </h5>
                        <p class="text-muted text-center">That pesky Instagram API is acting up.</p>
                        <div class="alert alert-warning">
                            <strong>Errors:</strong>
                            <ul class="mb-0">
                            {errors}
                            </ul>
                        </div>
                        <div class="alert alert-warning">
                            <strong>What you can do:</strong>
                            <ul class="mb-0">
                            {suggestions}
                            </ul>
                        </div>
                        <div class="d-grid gap-2 d-md-flex justify-content-md-center">
                            <a href="/" class="btn btn-outline-primary btn-lg">
                                <i class="fas fa-plus me-2"></i>Wait and/or Try Another Recipe
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </html>
    """


def get_status_page(queue_status: Dict[str, Any], mealie_url) -> str:
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>URL to Mealie - All Jobs Status</title>
        
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        
        <style>
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            
            .recipe-card {
                background: white;
                border-radius: 1rem;
                box-shadow: 0 1rem 3rem rgba(0,0,0,.1);
                border-top: 4px solid #667eea;
            }
            
            .logo-circle {
                width: 4rem;
                height: 4rem;
                background: linear-gradient(135deg, #667eea, #764ba2);
            }
            
            .btn-primary {
                background: linear-gradient(135deg, #667eea, #764ba2);
                border: none;
            }
            
            .btn-primary:hover {
                background: linear-gradient(135deg, #5a6fd8, #6b4190);
                transform: translateY(-1px);
            }
            
            .platform-badge {
                font-size: 0.8rem;
            }
            
            .feature-icon {
                color: #667eea;
            }
            
            .input-group-text {
                background: #f8f9fa;
                border-right: none;
            }
            
            .form-control {
                border-left: none;
            }
            
            .form-control:focus {
                border-color: #667eea;
                box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
            }
        </style>
    </head>
    <body class="d-flex py-4">
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <h1>All Jobs Status</h1>
                     <button onclick="location.href='/'" class="btn btn-secondary btn-lg w-100 d-flex align-items-center justify-content-center gap-2">
                            <i class="fas fa-magic"></i>
                            Back to Home
                    </button>
                    <div id="current">Loading data about current task...</div>
                    <br>
                    <div id="tasks">Loading queue...</div>
                </div>
            </div>
        </div>
        
        <script>
            async function updateStatus() {
                const res = await fetch('/status/json');
                const data = await res.json();

                const curr_task = data.currently_processing

                if (!curr_task) {
                    document.getElementById('current').innerHTML = `Nothing is processing at the moment!`;
                    document.getElementById('tasks').innerHTML = `No queued tasks!`;
                    return;
                }
                
                const startTime = curr_task.started_at ? new Date(curr_task.started_at).toLocaleTimeString() : '';
                        const error = curr_task.error ? `<br>Error: ${curr_task.error}` : '';
                        
                document.getElementById('current').innerHTML = `
                    <div class="curr_task current ${curr_task.status}">
                        <strong>${curr_task.status.toUpperCase()}</strong> - ${curr_task.url}
                        ${startTime ? `<br>Started: ${startTime}` : ''}
                        ${error}
                    </div>
                `;

                let html = `<p>Unfinished tasks: ${data.queue_count}</p>`;
                
                if (data.queued_tasks.length > 0) {
                    data.queued_tasks.forEach(task => {
                        const startTime = task.started_at ? new Date(task.started_at).toLocaleTimeString() : '';
                        const error = task.error ? `<br>Error: ${task.error}` : '';
                        
                        html += `
                            <div class="task ${task.status}">
                                <strong>${task.status.toUpperCase()}</strong> - ${task.url}
                                ${startTime ? `<br>Started: ${startTime}` : ''}
                                <br>Position in Queue: ${task.queue_position}
                                ${error}
                            </div>
                        `;
                    });
                } else {
                    html += `No queued tasks!`;
                }
                
                document.getElementById('tasks').innerHTML = html;
            }
            
            updateStatus();
            setInterval(updateStatus, 2000);
        </script>
    </body>
    </html>
    """
