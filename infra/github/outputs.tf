output "repository_node_id" {
  description = "GraphQL node ID of the repository — the handle branch protection binds to"
  value       = github_repository.this.node_id
}
