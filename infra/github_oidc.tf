# GitHub Actions -> AWS through OIDC. Both resources were created by hand and are imported here,
# so the trust policy lives in git. Used by .github/workflows/deploy.yml.

import {
  to = aws_iam_openid_connect_provider.github
  id = "arn:aws:iam::435466091082:oidc-provider/token.actions.githubusercontent.com"
}

import {
  to = aws_iam_role.github_actions_deploy
  id = "GitHubActionsDeployRole"
}

resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

resource "aws_iam_role" "github_actions_deploy" {
  name = "GitHubActionsDeployRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = aws_iam_openid_connect_provider.github.arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        # Only pushes to main of this repo. The repo uses immutable subjects (owner and repo IDs in the
        # claim), so a renamed or recreated repo cannot match; the old repo's ID is not this one.
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          "token.actions.githubusercontent.com:sub" = "repo:KevinLopezPastor@137914994/mlops-pipeline@1436065944:ref:refs/heads/main"
        }
      }
    }]
  })
}
