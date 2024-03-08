import pytest
from graphql_relay import to_global_id

from ..constants import TenantType, TenantUserRole
from ..models import TenantMembership


pytestmark = pytest.mark.django_db


class TestCreateTenantMutation:
    MUTATION = '''
        mutation CreateTenant($input: CreateTenantMutationInput!) {
          createTenant(input: $input) {
            tenant {
              id
              name
              slug
              type
              membership {
                role
                invitationAccepted
              }
            }
          }
        }
    '''

    def test_create_new_tenant(self, graphene_client, user):
        graphene_client.force_authenticate(user)
        executed = self.mutate(graphene_client, {"name": "Test"})
        response_data = executed["data"]["createTenant"]["tenant"]
        assert response_data["name"] == "Test"
        assert response_data["slug"] == "test"
        assert response_data["type"] == TenantType.ORGANIZATION
        assert response_data["membership"]["role"] == TenantUserRole.OWNER

    def test_create_new_tenant_with_same_name(self, graphene_client, user, tenant_factory):
        tenant_factory(name="Test", slug="test")
        graphene_client.force_authenticate(user)
        executed = self.mutate(graphene_client, {"name": "Test"})
        response_data = executed["data"]["createTenant"]["tenant"]
        assert response_data["name"] == "Test"
        assert response_data["slug"] == "test-1"
        assert response_data["type"] == TenantType.ORGANIZATION
        assert response_data["membership"]["role"] == TenantUserRole.OWNER

    def test_unauthenticated_user(self, graphene_client):
        executed = self.mutate(graphene_client, {"name": "Test"})
        assert executed["errors"][0]["message"] == "permission_denied"

    @classmethod
    def mutate(cls, graphene_client, data):
        return graphene_client.mutate(cls.MUTATION, variable_values={'input': data})


class TestUpdateTenantMutation:
    MUTATION = '''
        mutation UpdateTenant($input: UpdateTenantMutationInput!) {
          updateTenant(input: $input) {
            tenant {
              id
              name
              slug
              type
              membership {
                role
                invitationAccepted
              }
            }
          }
        }
    '''

    def test_update_tenant(self, graphene_client, user, tenant_factory, tenant_membership_factory):
        tenant = tenant_factory(name="Tenant 1", type=TenantType.ORGANIZATION)
        tenant_membership_factory(tenant=tenant, user=user, role=TenantUserRole.OWNER)
        graphene_client.force_authenticate(user)
        graphene_client.set_tenant_dependent_context(tenant, TenantUserRole.OWNER)
        executed = self.mutate(graphene_client, {"id": to_global_id("TenantType", tenant.id), "name": "Tenant 2"})
        response_data = executed["data"]["updateTenant"]["tenant"]
        assert response_data["name"] == "Tenant 2"
        assert response_data["slug"] == "tenant-2"
        assert response_data["type"] == TenantType.ORGANIZATION
        assert response_data["membership"]["role"] == TenantUserRole.OWNER

    def test_user_without_membership(self, graphene_client, user, tenant_factory):
        tenant = tenant_factory(name="Tenant 1", type=TenantType.ORGANIZATION)
        graphene_client.force_authenticate(user)
        graphene_client.set_tenant_dependent_context(tenant, None)
        executed = self.mutate(graphene_client, {"id": to_global_id("TenantType", tenant.id), "name": "Tenant 2"})
        assert executed["errors"][0]["message"] == "permission_denied"

    def test_user_with_admin_membership(self, graphene_client, user, tenant_factory, tenant_membership_factory):
        tenant = tenant_factory(name="Tenant 1", type=TenantType.ORGANIZATION)
        tenant_membership_factory(tenant=tenant, user=user, role=TenantUserRole.ADMIN)
        graphene_client.force_authenticate(user)
        graphene_client.set_tenant_dependent_context(tenant, TenantUserRole.ADMIN)
        executed = self.mutate(graphene_client, {"id": to_global_id("TenantType", tenant.id), "name": "Tenant 2"})
        assert executed["errors"][0]["message"] == "permission_denied"

    def test_user_with_member_membership(self, graphene_client, user, tenant_factory, tenant_membership_factory):
        tenant = tenant_factory(name="Tenant 1", type=TenantType.ORGANIZATION)
        tenant_membership_factory(tenant=tenant, user=user, role=TenantUserRole.MEMBER)
        graphene_client.force_authenticate(user)
        graphene_client.set_tenant_dependent_context(tenant, TenantUserRole.MEMBER)
        executed = self.mutate(graphene_client, {"id": to_global_id("TenantType", tenant.id), "name": "Tenant 2"})
        assert executed["errors"][0]["message"] == "permission_denied"

    def test_unauthenticated_user(self, graphene_client, tenant_factory):
        tenant = tenant_factory(name="Tenant 1")
        executed = self.mutate(graphene_client, {"id": to_global_id("TenantType", tenant.id), "name": "Tenant 2"})
        assert executed["errors"][0]["message"] == "permission_denied"

    @classmethod
    def mutate(cls, graphene_client, data):
        return graphene_client.mutate(cls.MUTATION, variable_values={'input': data})


class TestDeleteTenantMutation:
    MUTATION = '''
        mutation DeleteTenant($input: DeleteTenantMutationInput!) {
          deleteTenant(input: $input) {
            deletedIds
          }
        }
    '''

    def test_delete_tenant(self, graphene_client, user, tenant_factory, tenant_membership_factory):
        tenant = tenant_factory(name="Tenant 1", type=TenantType.ORGANIZATION)
        tenant_membership_factory(tenant=tenant, user=user, role=TenantUserRole.OWNER)
        graphene_client.force_authenticate(user)
        graphene_client.set_tenant_dependent_context(tenant, TenantUserRole.OWNER)
        executed = self.mutate(graphene_client, {"id": to_global_id("TenantType", tenant.id)})
        response_data = executed["data"]["deleteTenant"]["deletedIds"]
        assert response_data[0] == to_global_id("TenantType", tenant.id)

    def test_user_without_membership(self, graphene_client, user, tenant_factory):
        tenant = tenant_factory(name="Tenant 1", type=TenantType.ORGANIZATION)
        graphene_client.force_authenticate(user)
        graphene_client.set_tenant_dependent_context(tenant, None)
        executed = self.mutate(graphene_client, {"id": to_global_id("TenantType", tenant.id)})
        assert executed["errors"][0]["message"] == "permission_denied"

    def test_user_with_admin_membership(self, graphene_client, user, tenant_factory, tenant_membership_factory):
        tenant = tenant_factory(name="Tenant 1", type=TenantType.ORGANIZATION)
        tenant_membership_factory(tenant=tenant, user=user, role=TenantUserRole.ADMIN)
        graphene_client.force_authenticate(user)
        graphene_client.set_tenant_dependent_context(tenant, TenantUserRole.ADMIN)
        executed = self.mutate(graphene_client, {"id": to_global_id("TenantType", tenant.id)})
        assert executed["errors"][0]["message"] == "permission_denied"

    def test_user_with_member_membership(self, graphene_client, user, tenant_factory, tenant_membership_factory):
        tenant = tenant_factory(name="Tenant 1", type=TenantType.ORGANIZATION)
        tenant_membership_factory(tenant=tenant, user=user, role=TenantUserRole.MEMBER)
        graphene_client.force_authenticate(user)
        graphene_client.set_tenant_dependent_context(tenant, TenantUserRole.MEMBER)
        executed = self.mutate(graphene_client, {"id": to_global_id("TenantType", tenant.id)})
        assert executed["errors"][0]["message"] == "permission_denied"

    def test_unauthenticated_user(self, graphene_client, tenant_factory):
        tenant = tenant_factory(name="Tenant 1")
        executed = self.mutate(graphene_client, {"id": to_global_id("TenantType", tenant.id)})
        assert executed["errors"][0]["message"] == "permission_denied"

    @classmethod
    def mutate(cls, graphene_client, data):
        return graphene_client.mutate(cls.MUTATION, variable_values={'input': data})


class TestCreateTenantInvitationMutation:
    MUTATION = '''
    mutation CreateTenantInvitation($input: CreateTenantInvitationMutationInput!) {
      createTenantInvitation(input: $input) {
        ok
        email
        role
        tenantId
      }
    }
    '''

    def test_create_tenant_invitation_by_owner(
        self, mocker, graphene_client, user, tenant_factory, tenant_membership_factory
    ):
        make_token = mocker.patch(
            "apps.multitenancy.tokens.TenantInvitationTokenGenerator.make_token", return_value="token"
        )
        tenant = tenant_factory(name="Tenant 1", type=TenantType.ORGANIZATION)
        tenant_membership_factory(tenant=tenant, user=user, role=TenantUserRole.OWNER)
        graphene_client.force_authenticate(user)
        graphene_client.set_tenant_dependent_context(tenant, TenantUserRole.OWNER)
        executed = self.mutate(
            graphene_client,
            {
                "tenantId": to_global_id("TenantType", tenant.id),
                "email": "test@example.com",
                "role": TenantUserRole.ADMIN.upper(),
            },
        )
        response_data = executed["data"]["createTenantInvitation"]
        assert response_data["ok"] is True
        assert response_data["email"] == "test@example.com"
        assert response_data["role"] == TenantUserRole.ADMIN.upper()
        assert response_data["tenantId"] == to_global_id("TenantType", tenant.id)
        make_token.assert_called_once()

    def test_create_tenant_invitation_by_admin(self, graphene_client, user, tenant_factory, tenant_membership_factory):
        tenant = tenant_factory(name="Tenant 1", type=TenantType.ORGANIZATION)
        tenant_membership_factory(tenant=tenant, user=user, role=TenantUserRole.ADMIN)
        graphene_client.force_authenticate(user)
        graphene_client.set_tenant_dependent_context(tenant, TenantUserRole.ADMIN)
        executed = self.mutate(
            graphene_client,
            {
                "tenantId": to_global_id("TenantType", tenant.id),
                "email": "test@example.com",
                "role": TenantUserRole.ADMIN.upper(),
            },
        )
        assert executed["errors"][0]["message"] == "permission_denied"

    def test_create_tenant_invitation_by_member(self, graphene_client, user, tenant_factory, tenant_membership_factory):
        tenant = tenant_factory(name="Tenant 1", type=TenantType.ORGANIZATION)
        tenant_membership_factory(tenant=tenant, user=user, role=TenantUserRole.MEMBER)
        graphene_client.force_authenticate(user)
        graphene_client.set_tenant_dependent_context(tenant, TenantUserRole.MEMBER)
        executed = self.mutate(
            graphene_client,
            {
                "tenantId": to_global_id("TenantType", tenant.id),
                "email": "test@example.com",
                "role": TenantUserRole.ADMIN.upper(),
            },
        )
        assert executed["errors"][0]["message"] == "permission_denied"

    def test_user_without_membership(self, graphene_client, user, tenant_factory):
        tenant = tenant_factory(name="Tenant 1", type=TenantType.ORGANIZATION)
        graphene_client.force_authenticate(user)
        graphene_client.set_tenant_dependent_context(tenant, None)
        executed = self.mutate(
            graphene_client,
            {
                "tenantId": to_global_id("TenantType", tenant.id),
                "email": "test@example.com",
                "role": TenantUserRole.ADMIN.upper(),
            },
        )
        assert executed["errors"][0]["message"] == "permission_denied"

    def test_unauthenticated_user(self, graphene_client, tenant_factory):
        tenant = tenant_factory(name="Tenant 1")
        executed = self.mutate(
            graphene_client,
            {
                "tenantId": to_global_id("TenantType", tenant.id),
                "email": "test@example.com",
                "role": TenantUserRole.ADMIN.upper(),
            },
        )
        assert executed["errors"][0]["message"] == "permission_denied"

    @classmethod
    def mutate(cls, graphene_client, data):
        return graphene_client.mutate(cls.MUTATION, variable_values={'input': data})


class TestAcceptTenantInvitationMutation:
    MUTATION = '''
    mutation AcceptTenantInvitation($input: AcceptTenantInvitationMutationInput!) {
      acceptTenantInvitation(input: $input) {
        ok
      }
    }
    '''

    def test_accept_invitation_by_invitee(
        self, mocker, graphene_client, user, tenant_factory, tenant_membership_factory
    ):
        check_token = mocker.patch(
            "apps.multitenancy.tokens.TenantInvitationTokenGenerator.check_token", return_value=True
        )
        tenant = tenant_factory(name="Tenant 1", type=TenantType.ORGANIZATION)
        membership = tenant_membership_factory(tenant=tenant, user=user, role=TenantUserRole.MEMBER, is_accepted=False)
        graphene_client.force_authenticate(user)
        executed = self.mutate(
            graphene_client, {"id": to_global_id("TenantMembershipType", membership.id), "token": "token"}
        )
        response_data = executed["data"]["acceptTenantInvitation"]
        assert response_data["ok"] is True
        membership = TenantMembership.objects.filter(tenant=tenant, user=user).first()
        assert membership.is_accepted
        assert membership.invitation_accepted_at
        check_token.assert_called_once()

    def test_accept_invitation_by_invitee_wrong_token(
        self, mocker, graphene_client, user, tenant_factory, tenant_membership_factory
    ):
        check_token = mocker.patch(
            "apps.multitenancy.tokens.TenantInvitationTokenGenerator.check_token", return_value=False
        )
        tenant = tenant_factory(name="Tenant 1", type=TenantType.ORGANIZATION)
        membership = tenant_membership_factory(tenant=tenant, user=user, role=TenantUserRole.MEMBER, is_accepted=False)
        graphene_client.force_authenticate(user)
        executed = self.mutate(
            graphene_client, {"id": to_global_id("TenantMembershipType", membership.id), "token": "token"}
        )
        assert executed["errors"][0]["message"] == "GraphQlValidationError"
        check_token.assert_called_once()

    def test_accept_invitation_by_other_user(
        self, graphene_client, user_factory, tenant_factory, tenant_membership_factory
    ):
        logged_user = user_factory()
        invitee_user = user_factory()
        tenant = tenant_factory(name="Tenant 1", type=TenantType.ORGANIZATION)
        membership = tenant_membership_factory(
            tenant=tenant, user=invitee_user, role=TenantUserRole.MEMBER, is_accepted=False
        )
        graphene_client.force_authenticate(logged_user)
        executed = self.mutate(
            graphene_client, {"id": to_global_id("TenantMembershipType", membership.id), "token": "token"}
        )
        assert executed["errors"][0]["message"] == "Invitation not found."

    def test_unauthenticated_user(self, graphene_client, user, tenant_factory, tenant_membership_factory):
        tenant = tenant_factory(name="Tenant 1", type=TenantType.ORGANIZATION)
        membership = tenant_membership_factory(tenant=tenant, user=user, role=TenantUserRole.MEMBER, is_accepted=False)
        executed = self.mutate(
            graphene_client, {"id": to_global_id("TenantMembershipType", membership.id), "token": "token"}
        )
        assert executed["errors"][0]["message"] == "permission_denied"

    @classmethod
    def mutate(cls, graphene_client, data):
        return graphene_client.mutate(cls.MUTATION, variable_values={'input': data})


class TestDeclineTenantInvitationMutation:
    MUTATION = '''
    mutation DeclineTenantInvitation($input:DeclineTenantInvitationMutationInput!) {
      declineTenantInvitation(input: $input) {
        ok
      }
    }
    '''

    def test_decline_invitation_by_invitee(
        self, mocker, graphene_client, user, tenant_factory, tenant_membership_factory
    ):
        check_token = mocker.patch(
            "apps.multitenancy.tokens.TenantInvitationTokenGenerator.check_token", return_value=True
        )
        tenant = tenant_factory(name="Tenant 1", type=TenantType.ORGANIZATION)
        membership = tenant_membership_factory(tenant=tenant, user=user, role=TenantUserRole.MEMBER, is_accepted=False)
        graphene_client.force_authenticate(user)
        executed = self.mutate(
            graphene_client, {"id": to_global_id("TenantMembershipType", membership.id), "token": "token"}
        )
        response_data = executed["data"]["declineTenantInvitation"]
        assert response_data["ok"] is True
        assert not TenantMembership.objects.filter(tenant=tenant, user=user).exists()
        check_token.assert_called_once()

    def test_decline_invitation_by_invitee_wrong_token(
        self, mocker, graphene_client, user, tenant_factory, tenant_membership_factory
    ):
        check_token = mocker.patch(
            "apps.multitenancy.tokens.TenantInvitationTokenGenerator.check_token", return_value=False
        )
        tenant = tenant_factory(name="Tenant 1", type=TenantType.ORGANIZATION)
        membership = tenant_membership_factory(tenant=tenant, user=user, role=TenantUserRole.MEMBER, is_accepted=False)
        graphene_client.force_authenticate(user)
        executed = self.mutate(
            graphene_client, {"id": to_global_id("TenantMembershipType", membership.id), "token": "token"}
        )
        assert executed["errors"][0]["message"] == "GraphQlValidationError"
        check_token.assert_called_once()

    def test_decline_invitation_by_other_user(
        self, graphene_client, user_factory, tenant_factory, tenant_membership_factory
    ):
        logged_user = user_factory()
        invitee_user = user_factory()
        tenant = tenant_factory(name="Tenant 1", type=TenantType.ORGANIZATION)
        membership = tenant_membership_factory(
            tenant=tenant, user=invitee_user, role=TenantUserRole.MEMBER, is_accepted=False
        )
        graphene_client.force_authenticate(logged_user)
        executed = self.mutate(
            graphene_client, {"id": to_global_id("TenantMembershipType", membership.id), "token": "token"}
        )
        assert executed["errors"][0]["message"] == "Invitation not found."

    def test_unauthenticated_user(self, graphene_client, user, tenant_factory, tenant_membership_factory):
        tenant = tenant_factory(name="Tenant 1", type=TenantType.ORGANIZATION)
        membership = tenant_membership_factory(tenant=tenant, user=user, role=TenantUserRole.MEMBER, is_accepted=False)
        executed = self.mutate(
            graphene_client, {"id": to_global_id("TenantMembershipType", membership.id), "token": "token"}
        )
        assert executed["errors"][0]["message"] == "permission_denied"

    @classmethod
    def mutate(cls, graphene_client, data):
        return graphene_client.mutate(cls.MUTATION, variable_values={"input": data})


class TestAllTenantsQuery:
    def test_all_tenants_query(self, mocker, graphene_client, user, tenant_factory, tenant_membership_factory):
        query = """
        query getAllTenants {
            allTenants {
                edges {
                    node {
                        id
                        name
                        slug
                        type
                        membership {
                            id
                            role
                            invitationAccepted
                            userId
                            inviteeEmailAddress
                            username
                            invitationToken
                        }
                        userMemberships {
                            id
                            role
                            invitationAccepted
                            userId
                            inviteeEmailAddress
                            username
                            invitationToken
                        }
                    }
                }
            }
        }
        """
        tenant_factory.create_batch(10)
        make_token = mocker.patch(
            "apps.multitenancy.tokens.TenantInvitationTokenGenerator.make_token", return_value="token"
        )
        default_user_tenant = user.tenants.first()
        tenant_with_invitation = tenant_factory(name="Invitation Tenant", type=TenantType.ORGANIZATION)
        tenants = [
            default_user_tenant,
            tenant_with_invitation,
            tenant_factory(name="Test tenant", type=TenantType.ORGANIZATION),
            tenant_factory(name="Test tenant 2", type=TenantType.ORGANIZATION),
        ]
        default_user_tenant_membership = TenantMembership.objects.filter(user=user, tenant=default_user_tenant).first()
        invitation_membership = tenant_membership_factory(
            tenant=tenant_with_invitation, role=TenantUserRole.ADMIN, user=user, is_accepted=False
        )
        memberships = [
            default_user_tenant_membership,
            invitation_membership,
            tenant_membership_factory(tenant=tenants[2], role=TenantUserRole.OWNER, user=user),
            tenant_membership_factory(tenant=tenants[3], role=TenantUserRole.MEMBER, user=user),
        ]
        graphene_client.force_authenticate(user)
        graphene_client.set_tenant_dependent_context(None, None)
        executed = graphene_client.query(query)
        executed_tenants = executed["data"]["allTenants"]["edges"]
        for idx, executed_tenant in enumerate(executed_tenants):
            assert executed_tenant["node"]["id"] == to_global_id("TenantType", tenants[idx].id)
            assert executed_tenant["node"]["name"] == tenants[idx].name
            assert executed_tenant["node"]["slug"] == tenants[idx].slug
            assert executed_tenant["node"]["type"] == tenants[idx].type
            assert executed_tenant["node"]["userMemberships"] is None
            assert executed_tenant["node"]["membership"]["id"] == to_global_id(
                "TenantMembershipType", memberships[idx].id
            )
            assert executed_tenant["node"]["membership"]["role"] == memberships[idx].role
            assert executed_tenant["node"]["membership"]["invitationAccepted"] == memberships[idx].is_accepted
            assert executed_tenant["node"]["membership"]["userId"] == user.id
            assert executed_tenant["node"]["membership"]["username"] == str(user.profile)
            if memberships[idx].is_accepted:
                assert executed_tenant["node"]["membership"]["invitationToken"] is None
            else:
                assert executed_tenant["node"]["membership"]["invitationToken"] == "token"

        make_token.assert_called_once()

    def test_all_tenants_query_unauthenticated_user(self, graphene_client):
        query = """
        query getAllTenants {
            allTenants {
                edges {
                    node {
                        id
                        name
                        slug
                        type
                        membership {
                            id
                            role
                            invitationAccepted
                            userId
                            inviteeEmailAddress
                            username
                            invitationToken
                        }
                    }
                }
            }
        }
        """
        executed = graphene_client.query(query)
        assert executed["errors"][0]["message"] == "permission_denied"


class TestTenantQuery:
    def test_tenant_query(self, graphene_client, user, user_factory, tenant_factory, tenant_membership_factory):
        query = """
        query getTenant($id: ID!) {
          tenant(id: $id) {
            id
            name
            slug
            type
            membership {
              id
              role
              invitationAccepted
              userId
              inviteeEmailAddress
              username
              invitationToken
            }
            userMemberships {
              id
              role
              invitationAccepted       
              userId
              inviteeEmailAddress
              invitationToken
              username
            }
          }
        }
        """
        tenant_factory.create_batch(10)
        tenant = tenant_factory(name="Test tenant", type=TenantType.ORGANIZATION)
        membership = tenant_membership_factory(tenant=tenant, role=TenantUserRole.OWNER, user=user)
        tenant_users = user_factory.create_batch(5)
        for tenant_user in tenant_users:
            tenant_membership_factory(tenant=tenant, role=TenantUserRole.MEMBER, user=tenant_user)
        tenant_invited_users = user_factory.create_batch(5)
        for tenant_user in tenant_invited_users:
            tenant_membership_factory(tenant=tenant, role=TenantUserRole.MEMBER, user=tenant_user, is_accepted=False)
        graphene_client.force_authenticate(user)
        graphene_client.set_tenant_dependent_context(tenant=tenant, role=TenantUserRole.OWNER)
        executed = graphene_client.query(query, variable_values={"id": to_global_id("TenantType", tenant.pk)})
        executed_tenant = executed["data"]["tenant"]
        assert executed_tenant["id"] == to_global_id("TenantType", tenant.id)
        assert executed_tenant["name"] == tenant.name
        assert executed_tenant["slug"] == tenant.slug
        assert executed_tenant["type"] == tenant.type
        assert len(executed_tenant["userMemberships"]) == 11
        for user_membership in executed_tenant["userMemberships"]:
            assert user_membership["invitationToken"] is None
        assert executed_tenant["membership"]["id"] == to_global_id("TenantMembershipType", membership.id)
        assert executed_tenant["membership"]["role"] == membership.role
        assert executed_tenant["membership"]["invitationAccepted"] == membership.is_accepted
        assert executed_tenant["membership"]["userId"] == user.id
        assert executed_tenant["membership"]["username"] == str(user.profile)
        assert executed_tenant["membership"]["invitationToken"] is None

    def test_tenant_query_user_with_invitation(
        self, mocker, graphene_client, user, user_factory, tenant_factory, tenant_membership_factory
    ):
        query = """
        query getTenant($id: ID!) {
          tenant(id: $id) {
            id
            name
            slug
            type
            membership {
              id
              role
              invitationAccepted
              userId
              inviteeEmailAddress
              username
              invitationToken
            }
            userMemberships {
              id
              role
              invitationAccepted       
              userId
              inviteeEmailAddress
              invitationToken
              username
            }
          }
        }
        """
        tenant_factory.create_batch(10)
        make_token = mocker.patch(
            "apps.multitenancy.tokens.TenantInvitationTokenGenerator.make_token", return_value="token"
        )
        tenant = tenant_factory(name="Test tenant", type=TenantType.ORGANIZATION)
        membership = tenant_membership_factory(tenant=tenant, role=TenantUserRole.OWNER, user=user, is_accepted=False)
        tenant_users = user_factory.create_batch(5)
        for tenant_user in tenant_users:
            tenant_membership_factory(tenant=tenant, role=TenantUserRole.MEMBER, user=tenant_user)
        graphene_client.force_authenticate(user)
        graphene_client.set_tenant_dependent_context(tenant=tenant, role=None)
        executed = graphene_client.query(query, variable_values={"id": to_global_id("TenantType", tenant.pk)})
        executed_tenant = executed["data"]["tenant"]
        assert executed_tenant["id"] == to_global_id("TenantType", tenant.id)
        assert executed_tenant["name"] == tenant.name
        assert executed_tenant["slug"] == tenant.slug
        assert executed_tenant["type"] == tenant.type
        assert executed_tenant["userMemberships"] is None
        assert executed_tenant["membership"]["id"] == to_global_id("TenantMembershipType", membership.id)
        assert executed_tenant["membership"]["role"] == membership.role
        assert executed_tenant["membership"]["invitationAccepted"] == membership.is_accepted
        assert executed_tenant["membership"]["userId"] == user.id
        assert executed_tenant["membership"]["username"] == str(user.profile)
        assert executed_tenant["membership"]["invitationToken"] == "token"
        # No permissions for userMemberships for not accepted invitation
        assert executed["errors"][0]["message"] == "permission_denied"
        make_token.assert_called_once()

    def test_tenant_query_user_without_membership(
        self, graphene_client, user, user_factory, tenant_factory, tenant_membership_factory
    ):
        query = """
        query getTenant($id: ID!) {
          tenant(id: $id) {
            id
            name
            slug
            type
            membership {
              id
              role
              invitationAccepted
              userId
              inviteeEmailAddress
              username
              invitationToken
            }
            userMemberships {
              id
              role
              invitationAccepted       
              userId
              inviteeEmailAddress
              invitationToken
              username
            }
          }
        }
        """
        tenant_factory.create_batch(10)
        tenant = tenant_factory(name="Test tenant", type=TenantType.ORGANIZATION)
        tenant_users = user_factory.create_batch(5)
        for tenant_user in tenant_users:
            tenant_membership_factory(tenant=tenant, role=TenantUserRole.MEMBER, user=tenant_user)
        graphene_client.force_authenticate(user)
        graphene_client.set_tenant_dependent_context(tenant=tenant, role=None)
        executed = graphene_client.query(query, variable_values={"id": to_global_id("TenantType", tenant.pk)})
        assert executed["data"]["tenant"] is None

    def test_tenant_query_unauthenticated_user(
        self, graphene_client, user_factory, tenant_factory, tenant_membership_factory
    ):
        query = """
        query getTenant($id: ID!) {
          tenant(id: $id) {
            id
            name
            slug
            type
            membership {
              id
              role
              invitationAccepted
              userId
              inviteeEmailAddress
              username
              invitationToken
            }
            userMemberships {
              id
              role
              invitationAccepted       
              userId
              inviteeEmailAddress
              invitationToken
              username
            }
          }
        }
        """
        tenant_factory.create_batch(10)
        tenant = tenant_factory(name="Test tenant", type=TenantType.ORGANIZATION)
        tenant_users = user_factory.create_batch(5)
        for tenant_user in tenant_users:
            tenant_membership_factory(tenant=tenant, role=TenantUserRole.MEMBER, user=tenant_user)
        executed = graphene_client.query(query, variable_values={"id": to_global_id("TenantType", tenant.pk)})
        assert executed["errors"][0]["message"] == "permission_denied"
