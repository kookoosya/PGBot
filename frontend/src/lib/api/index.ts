/**
 * API entry point: HTTP client + domain modules merged into a single `api` singleton.
 */

import { HttpClient } from "./client";
import { createAuthApi, type AuthApi } from "./auth";
import { createIssuesApi, type IssuesApi } from "./issues";
import { createClassifiedsApi, type ClassifiedsApi } from "./classifieds";
import { createPlacesApi, type PlacesApi } from "./places";
import { createServicesApi, type ServicesApi } from "./services";
import { createAdminApi, type AdminApi } from "./admin";
import { createAiApi, type AiApi } from "./ai";
import { createPublicApi, type PublicApi } from "./public";

export * from "./types";
export type { AuthScope } from "./client";
export { API_BASE } from "./client";

type CrossDomainApi = {
  getServiceClassifieds(params?: Record<string, string>): ReturnType<ClassifiedsApi["getClassifieds"]>;
};

export type ApiClient = HttpClient &
  AuthApi &
  IssuesApi &
  ClassifiedsApi &
  PlacesApi &
  ServicesApi &
  AdminApi &
  AiApi &
  PublicApi &
  CrossDomainApi;

function createApiClient(): ApiClient {
  const client = new HttpClient();
  const classifieds = createClassifiedsApi(client);

  return Object.assign(
    client,
    createAuthApi(client),
    createIssuesApi(client),
    classifieds,
    createPlacesApi(client),
    createServicesApi(client),
    createAdminApi(client),
    createAiApi(client),
    createPublicApi(client),
    {
      getServiceClassifieds(params?: Record<string, string>) {
        return classifieds.getClassifieds({ ...params, services_only: "true", page_size: "50" });
      },
    },
  ) as ApiClient;
}

export const api = createApiClient();
