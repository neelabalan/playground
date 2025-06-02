use axum::{Router, routing::get};
use chrono::prelude::*;
use std::env;
use std::fs;

fn get_color(color: &str) -> &'static str {
    match color {
        "red" => "🔴",
        "orange" => "🟠",
        "yellow" => "🟡",
        "green" => "🟢",
        "blue" => "🔵",
        "purple" => "🟣",
        "brown" => "🟤",
        "black" => "⚫",
        "white" => "⚪",
        _ => "❓",
    }
}

fn get_hostname() -> String {
    // match env::var(key) {
    //     Ok(val) => println!("{}: {:?}", key, val),
    //     Err(e) => println!("couldn't interpret {}: {}", key, e),
    // }
    env::var("HOSTNAME").unwrap()
}

fn get_namespace() -> String {
    match env::var("NAMESPACE") {
        Ok(val) if !val.is_empty() => {
            fs::read_to_string("/var/nun/secrets/kubernetes.io/serviceaccount/namespace")
                .unwrap_or(val)
        }
        Ok(val) => val,
        Err(_) => String::from("?"),
    }
}

#[tokio::main]
async fn main() {
    let args: Vec<String> = env::args().collect();
    let color: String = args.get(1).cloned().unwrap_or("blue".to_string());
    let custom_text: String = args.get(2).cloned().unwrap_or("Hi there!".to_string());

    const PORT: u16 = 3000;
    let app = Router::new().route(
        "/",
        get({
            move || async move {
                format!(
                    "[{time}][{namespace}][{host}] {color} -- {text}\n",
                    time = Utc::now(),
                    namespace = get_namespace(),
                    host = get_hostname(),
                    color = get_color(&color),
                    text = custom_text
                )
            }
        }),
    );

    let listener = tokio::net::TcpListener::bind(format!("0.0.0.0:{}", PORT))
        .await
        .unwrap();
    println!("Starting HTTP server on port {}", PORT);
    // let namespace = get_namespace();
    // let hostname = get_hostname();
    axum::serve(listener, app).await.unwrap();
}
