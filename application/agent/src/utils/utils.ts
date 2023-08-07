export const extractPeerDomain = (clientName: string) => {
    const regex = /[\w]*.*(org[\d]+\.example\.com)/gm
    const matches = regex.exec(clientName)
    return matches?.[1]
}

export const extractOrg = (peerDomain: string) => {
    const regex = /(org[\d]+)/gm
    const matches = regex.exec(peerDomain)
    return matches?.[1]
}